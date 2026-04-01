import pandas as pd
import requests

def _call_vs_bctc(symbol: str) -> str:
    """Lazy import vietstock BCTC to avoid module path issues with uvicorn."""
    try:
        from services.vietstock_bctc_service import get_bctc_for_ai
        return get_bctc_for_ai(symbol)
    except Exception as e:
        print(f'[WARN] vietstock_bctc_service: {e}')
        return ''


class FundamentalService:
    """
    Layer 3: Cơ bản (Fundamental) - Trọng số 15%
    Định giá theo phương pháp Tầm Soát Trường Money:
      Fair Value = EPS Thực × P/E Ngành
      Margin of Safety zones: Mua Mạnh (-25%), Tích Lũy (-15%), Giữ, Chốt (+15%), Mạnh (+30%)
    """

    @staticmethod
    def _round_to_tick(price: float) -> float:
        # Bước giá chuẩn HOSE/HNX
        if price < 10000:
            return round(price / 10) * 10
        elif price < 50000:
            return round(price / 50) * 50
        else:
            return round(price / 100) * 100

    @staticmethod
    def _get_industry_pe(symbol: str) -> float:
        banks       = ["VCB","BID","CTG","MBB","ACB","VPB","TCB","STB","HDB","VIB","TPB","SHB","EIB","MSB","OCB","SSB","LPB","NAB"]
        securities  = ["SSI","VND","VCI","HCM","SHS","VIX","FTS","MBS","CTS","BSI","AGR"]
        real_estate = ["VHM","VIC","NVL","KDH","DIG","DXG","PDR","NLG","CEO","HDG","CRE","SCR","TCH","KBC","HAG"]
        steel       = ["HPG","HSG","NKG","SMC","TLH","VGS"]
        retail      = ["MWG","PNJ","FRT","DGW","PET","VRE","MSN"]
        tech        = ["FPT","CMG","ELC"]
        if symbol in banks:       return 10.5
        if symbol in securities:  return 18.0
        if symbol in real_estate: return 22.0
        if symbol in steel:       return 12.5
        if symbol in retail:      return 25.0
        if symbol in tech:        return 20.0
        return 15.0

    @staticmethod
    def _get_industry_pb(symbol: str) -> float:
        banks       = ["VCB","BID","CTG","MBB","ACB","VPB","TCB","STB","HDB","VIB","TPB","SHB","EIB","MSB","OCB","SSB","LPB","NAB"]
        securities  = ["SSI","VND","VCI","HCM","SHS","VIX","FTS","MBS","CTS","BSI","AGR"]
        real_estate = ["VHM","VIC","NVL","KDH","DIG","DXG","PDR","NLG","CEO","HDG","CRE","SCR","TCH","KBC","HAG"]
        steel       = ["HPG","HSG","NKG","SMC","TLH","VGS"]
        retail      = ["MWG","PNJ","FRT","DGW","PET","VRE","MSN"]
        tech        = ["FPT","CMG","ELC"]
        if symbol in banks:       return 1.5
        if symbol in securities:  return 1.8
        if symbol in real_estate: return 1.5
        if symbol in steel:       return 1.2
        if symbol in retail:      return 2.5
        if symbol in tech:        return 2.0
        return 1.5

    @staticmethod
    def _pe_label(current_pe: float, industry_pe: float) -> str:
        ratio = current_pe / industry_pe if industry_pe > 0 else 1.0
        if ratio < 0.75:   return "🟢 Rất Rẻ (Chiết khấu sâu so ngành)"
        elif ratio < 0.90: return "🟢 Rẻ (Ngưỡng hấp dẫn)"
        elif ratio <= 1.10: return "🟡 Hợp Lý (Ngang định giá ngành)"
        elif ratio <= 1.30: return "🟠 Hơi Đắt (Trên Trung bình Ngành)"
        else:               return "🔴 Đắt (Đếm rủi ro biên chất lượng)"

    @staticmethod
    def _get_default_eps(symbol: str, current_price: float = 0.0) -> float:
        """EPS baseline theo ngành khi không lấy được BCTC thực."""
        pe = FundamentalService._get_industry_pe(symbol)
        if current_price > 0:
            return (current_price * 1.15) / pe
        banks       = ["VCB","BID","CTG","MBB","ACB","VPB","TCB","STB","HDB","VIB","TPB","SHB","EIB","MSB","OCB","SSB","LPB","NAB"]
        securities  = ["SSI","VND","VCI","HCM","SHS","VIX","FTS","MBS","CTS","BSI","AGR"]
        real_estate = ["VHM","VIC","NVL","KDH","DIG","DXG","PDR","NLG","CEO","HDG","CRE","SCR","TCH","KBC","HAG"]
        steel       = ["HPG","HSG","NKG","SMC","TLH","VGS"]
        retail      = ["MWG","PNJ","FRT","DGW","PET","VRE","MSN"]
        tech        = ["FPT","CMG","ELC"]
        if symbol in banks:       return 2800.0
        if symbol in securities:  return 1800.0
        if symbol in real_estate: return 1200.0
        if symbol in steel:       return 3200.0
        if symbol in retail:      return 2000.0
        if symbol in tech:        return 4500.0
        return 1500.0

    @staticmethod
    def _build_mos_zones(fair_value: float, current_price: float) -> dict:
        """
        Margin of Safety zones theo phương pháp Tầm Soát Trường Money.
        Biên an toàn tính từ Fair Value (= Forward EPS × P/E Ngành).
        """
        rt = FundamentalService._round_to_tick
        
        # SMART MoS: Nếu giá thị trường đã rơi rất sâu (< 80% Fair Value),
        # Neo vùng mua theo đồ thị Technical (Giá hiện tại) thay vì Fair Value
        # Để tránh việc "giá 16k mà báo vùng mua mạnh 32k"
        if current_price > 0.0 and current_price < fair_value * 0.80:
            buy_strong = rt(current_price * 0.93)   # Mua Mạnh: Hỗ trợ đáy ngắn hạn (-7%)
            buy_zone   = rt(current_price * 1.05)   # Tích Lũy: Gom quanh nền (+5%)
            hold_top   = rt(fair_value * 0.90)      # Nắm Giữ: Canh target 1
            tp_zone    = rt(fair_value * 1.00)      # Chốt Lời: Về Fair Value
            tp_strong  = rt(fair_value * 1.15)      # Chốt Mạnh: Kéo thốc FOMO
        else:
            # Logic cơ bản: Chiết khấu từ Fair Value
            buy_strong = rt(fair_value * 0.75)   # Mua Mạnh: -25%
            buy_zone   = rt(fair_value * 0.85)   # Tích Lũy: -15%
            hold_top   = rt(fair_value * 1.00)   # Fair Value
            tp_zone    = rt(fair_value * 1.15)   # Chốt Lời: +15%
            tp_strong  = rt(fair_value * 1.30)   # Chốt Mạnh: +30%

        # Xác định vị trí hiện tại
        p = current_price
        if p <= 0:
            zone_label, action = "⬜ Chưa xác định", "QUAN SÁT"
        elif p <= buy_strong:
            zone_label, action = "🟢 Vùng Mua Mạnh (Đáy chiết khấu)", "MUA MẠNH"
        elif p <= buy_zone:
            zone_label, action = "🟢 Vùng Tích Lũy (An Toàn)", "TÍCH LŨY"
        elif p <= hold_top:
            zone_label, action = "🟡 Vùng Giữ (Gần Fair Value)", "NẮM GIỮ"
        elif p <= tp_zone:
            zone_label, action = "🟠 Vùng Trung Lập (Tạm chốt lời)", "CHỐT MỘT PHẦN"
        else:
            zone_label, action = "🔴 Vùng Rủi ro (Vượt giá trị cơ bản)", "TRÁNH/BÁN"

        return {
            "buy_strong":         buy_strong,
            "buy_zone":           buy_zone,
            "fair_value":         fair_value,   # Luôn là FV thực sự, không phải hold_top
            "tp_zone":            tp_zone,
            "tp_strong":          tp_strong,
            "current_zone_label": zone_label,
            "action":             action,
        }

    @staticmethod
    def analyze(symbol: str, current_price: float = 0.0) -> dict:
        try:
            def safe_get(v, default):
                try:
                    f = float(v)
                    return default if pd.isna(f) else f
                except:
                    return default

            pe_actual  = 0.0
            pb         = 1.5
            roe        = 0.15
            eps_actual = 0.0
            yoy_growth = 0.0
            hist_avg_pe = 0.0

            # ── VCI GraphQL: PE, PB, ROE, EPS, netProfitGrowth ──
            # Gọi thẳng VCI endpoint — không cần vnstock library
            _VCI_GQL = 'https://trading.vietcap.com.vn/data-mt/graphql'
            _VCI_HEADERS = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7',
                'Origin': 'https://trading.vietcap.com.vn',
                'Referer': 'https://trading.vietcap.com.vn/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            _GQL_QUERY = """
query Q($ticker: String!, $period: String!) {
  CompanyFinancialRatio(ticker: $ticker, period: $period) {
    ratio {
      yearReport
      revenue
      ebit
      grossMargin
      ebitMargin
      netProfit
      netProfitGrowth
      eps
      epsTTM
      pe
      pb
      roe
      roa
      currentRatio
      dividend
    }
  }
}
"""
            bctc_history = []  # Lịch sử 5 năm BCTC để Gemini phân tích xu hướng
            try:
                resp = requests.post(
                    _VCI_GQL,
                    json={'query': _GQL_QUERY, 'variables': {'ticker': symbol, 'period': 'Y'}},
                    headers=_VCI_HEADERS,
                    timeout=20
                )
                print(f"[{symbol}] VCI GQL status={resp.status_code} len={len(resp.text)}")
                if not resp.text.strip():
                    print(f"[{symbol}] VCI GQL empty body")
                else:
                    gql_data = resp.json()
                ratio_list = gql_data.get('data', {}).get('CompanyFinancialRatio', {}).get('ratio', [])
                print(f"[{symbol}] VCI ratio rows={len(ratio_list)}")
                if ratio_list:
                    # Sort newest-first by yearReport
                    ratio_list.sort(key=lambda x: x.get('yearReport', 0), reverse=True)
                    latest = ratio_list[0]
                    print(f"[{symbol}] VCI latest: {latest}")
                    pe_actual   = safe_get(latest.get('pe'),  0.0)
                    pb          = safe_get(latest.get('pb'),  1.5)
                    roe         = safe_get(latest.get('roe'), 0.15)
                    eps_actual  = safe_get(latest.get('epsTTM') or latest.get('eps'), 0.0)
                    if 0 < eps_actual < 50: eps_actual *= 1000  # nghìn đồng → đồng
                    # netProfitGrowth từ VCI là decimal (0.25 = 25%) hoặc % (25 = 25%)
                    raw_yoy = safe_get(latest.get('netProfitGrowth'), 0.0)
                    if raw_yoy != 0.0:
                        yoy_growth = raw_yoy / 100 if abs(raw_yoy) > 5 else raw_yoy
                    # Fallback YoY nếu netProfitGrowth = 0: tính từ 2 năm LNST
                    if yoy_growth == 0.0 and len(ratio_list) >= 2:
                        lnst_now  = safe_get(ratio_list[0].get('netProfit'), 0.0)
                        lnst_prev = safe_get(ratio_list[1].get('netProfit'), 0.0)
                        if lnst_prev != 0:
                            yoy_growth = (lnst_now - lnst_prev) / abs(lnst_prev)
                    print(f"[{symbol}] PE={pe_actual}, PB={pb}, ROE={roe}, EPS={eps_actual}, YoY={yoy_growth*100:.1f}%")
                    # Lịch sử PE 5 năm gần nhất từ VCI
                    pe_hist = [safe_get(x.get('pe'), 0.0) for x in ratio_list[:5] if safe_get(x.get('pe'), 0.0) > 0.1]
                    hist_avg_pe = round(sum(pe_hist) / len(pe_hist), 2) if pe_hist else 0.0
                    print(f"[{symbol}] Historical avg PE (5yr): {hist_avg_pe}")
                    # Build BCTC history for Gemini trend analysis (up to 5 years)
                    for row in ratio_list[:5]:
                        bctc_history.append({
                            'year':         row.get('yearReport'),
                            'revenue_bn':   round(safe_get(row.get('revenue'), 0) / 1e9, 1),
                            'ebit_bn':      round(safe_get(row.get('ebit'), 0) / 1e9, 1),
                            'netProfit_bn': round(safe_get(row.get('netProfit'), 0) / 1e9, 1),
                            'grossMargin':  round(safe_get(row.get('grossMargin'), 0) * 100, 1),
                            'ebitMargin':   round(safe_get(row.get('ebitMargin'), 0) * 100, 1),
                            'roe_pct':      round(safe_get(row.get('roe'), 0) * 100, 1),
                            'roa_pct':      round(safe_get(row.get('roa'), 0) * 100, 1),
                            'currentRatio': round(safe_get(row.get('currentRatio'), 0), 2),
                            'eps':          round(safe_get(row.get('epsTTM') or row.get('eps'), 0), 0),
                            'pe':           round(safe_get(row.get('pe'), 0), 1),
                            'pb':           round(safe_get(row.get('pb'), 0), 2),
                            'yoy_pct':      round(safe_get(row.get('netProfitGrowth'), 0) * 100, 1),
                        })
                else:
                    hist_avg_pe = 0.0
                    print(f"[{symbol}] VCI ratio empty. full_resp={str(gql_data)[:300]}")
            except Exception as gql_e:
                print(f"[{symbol}] VCI GQL EXCEPTION: {gql_e}")

            # ── Quarterly data: last 8 quarters for Gemini trend analysis ──
            q_history = []
            try:
                _GQL_QUARTERLY = """
query Q($ticker: String!, $period: String!) {
  CompanyFinancialRatio(ticker: $ticker, period: $period) {
    ratio {
      yearReport
      lengthReport
      revenue
      ebit
      grossMargin
      ebitMargin
      netProfit
      eps
      roe
      currentRatio
    }
  }
}
"""
                resp_q = requests.post(
                    _VCI_GQL,
                    json={'query': _GQL_QUARTERLY, 'variables': {'ticker': symbol, 'period': 'Q'}},
                    headers=_VCI_HEADERS,
                    timeout=20
                )
                if resp_q.status_code == 200:
                    q_data = resp_q.json()
                    q_list = q_data.get('data', {}).get('CompanyFinancialRatio', {}).get('ratio', [])
                    q_list.sort(key=lambda x: (x.get('yearReport', 0), x.get('lengthReport', 0)), reverse=True)
                    for qrow in q_list[:8]:  # 8 quarters = 2 years
                        q_history.append({
                            'period':       f"Q{qrow.get('lengthReport')}/{qrow.get('yearReport')}",
                            'revenue_bn':   round(safe_get(qrow.get('revenue'), 0) / 1e9, 1),
                            'ebit_bn':      round(safe_get(qrow.get('ebit'), 0) / 1e9, 1),
                            'netProfit_bn': round(safe_get(qrow.get('netProfit'), 0) / 1e9, 1),
                            'grossMargin':  round(safe_get(qrow.get('grossMargin'), 0) * 100, 1),
                            'ebitMargin':   round(safe_get(qrow.get('ebitMargin'), 0) * 100, 1),
                            'eps_q':        round(safe_get(qrow.get('eps'), 0), 0),
                        })
                    print(f"[{symbol}] Quarterly data: {len(q_history)} quarters fetched")
            except Exception as qe:
                print(f"[{symbol}] Quarterly fetch error: {qe}")

            industry_pe = FundamentalService._get_industry_pe(symbol)
            industry_pb = FundamentalService._get_industry_pb(symbol)
            book_value_per_share = (eps_actual * pe_actual / pb) if pb > 0 else 0.0
            pe_eval     = FundamentalService._pe_label(pe_actual if pe_actual > 0 else industry_pe, industry_pe)

            if eps_actual > 0:
                fair_value = FundamentalService._round_to_tick(eps_actual * industry_pe)
            else:
                fair_value = FundamentalService._round_to_tick(current_price * 1.15)

            upside    = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0
            mos_zones = FundamentalService._build_mos_zones(fair_value, current_price)

            # Vietstock BCTC balance sheet detail (inventory, advance payments, debt)
            bctc_vietstock = _call_vs_bctc(symbol)

            score = 50
            if 0 < pe_actual < industry_pe * 0.8: score += 15
            elif pe_actual > industry_pe * 1.3:    score -= 15
            elif pe_actual <= 0:                   score -= 25
            if roe > 0.15:   score += 20
            elif roe < 0.05: score -= 15
            if 0 < pb <= 1.2:  score += 15
            elif pb > 3.5:     score -= 15
            if yoy_growth > 0.15: score += 10
            elif yoy_growth < 0:  score -= 10

            return {
                "score": max(0, min(100, score)),
                "metrics": {
                    "PE":            round(pe_actual, 2),
                    "PB":            round(pb, 2),
                    "EPS":           round(eps_actual, 2),
                    "ROE_Percent":   round(roe * 100, 2),
                    "Fair_Value":    fair_value,
                    "Upside":        round(upside, 2),
                    "Reference_Price": fair_value,
                    "AI_Reasoning":  f"EPS thực={eps_actual:,.0f} VNĐ | P/E thị trường={pe_actual:.1f} ({pe_eval}) | Tăng trưởng YoY={yoy_growth*100:.1f}% | Fair Value tính theo P/E ngành {industry_pe}x.",
                    "mos_zones":     mos_zones,
                    "pe_evaluation": pe_eval,
                    "yoy_growth_pct": round(yoy_growth * 100, 2),
                    "industry_pe":   industry_pe,
                    "actual_pe":     round(pe_actual, 2),
                    "hist_avg_pe":   round(hist_avg_pe, 2),
                    "trailing_eps":  round(eps_actual, 2),
                    "pb_actual":     round(pb, 2),
                    "industry_pb":   round(industry_pb, 2),
                    "book_value_per_share": round(book_value_per_share, 2),
                    "bctc_history":  bctc_history,
                    "q_history":     q_history,
                    "bctc_vietstock": bctc_vietstock,
                },
                "status": "Healthy 🟢" if score >= 60 else ("Warning 🔴" if score < 40 else "Neutral 🟡")
            }

        except Exception as e:
            print(f"[{symbol}] Fundamental fallback triggered: {e}")
            fallback_pe  = FundamentalService._get_industry_pe(symbol)
            fallback_eps = FundamentalService._get_default_eps(symbol, current_price)
            fair_value   = FundamentalService._round_to_tick(fallback_eps * fallback_pe)
            upside       = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 15.0
            mos_zones    = FundamentalService._build_mos_zones(fair_value, current_price)
            pe_eval      = "🟡 Proxy Ngành (Chờ BCTC thực)"

            return {
                "score": 50,
                "metrics": {
                    "PE":            round(fallback_pe, 2),
                    "PB":            1.5,
                    "EPS":           round(fallback_eps, 2),
                    "ROE_Percent":   15.0,
                    "Fair_Value":    fair_value,
                    "Upside":        round(upside, 2),
                    "Reference_Price": fair_value,
                    "AI_Reasoning":  f"Dùng EPS proxy ngành ({fallback_eps:,.0f}) × P/E ngành ({fallback_pe}x). Cần BCTC thực để chính xác hơn.",
                    "mos_zones":     mos_zones,
                    "pe_evaluation": pe_eval,
                    "yoy_growth_pct": 0.0,
                    "industry_pe":   fallback_pe,
                    "pb_actual":     1.5,
                    "industry_pb":   1.5,
                    "book_value_per_share": 10000.0,
                },
                "status": "Proxy 🟡"
            }


fundamental_service = FundamentalService()
