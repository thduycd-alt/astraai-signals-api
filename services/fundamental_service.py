from vnstock import financial_ratio
import pandas as pd

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
            "fair_value":         hold_top,
            "tp_zone":            tp_zone,
            "tp_strong":          tp_strong,
            "current_zone_label": zone_label,
            "action":             action,
        }

    @staticmethod
    def analyze(symbol: str, current_price: float = 0.0) -> dict:
        try:
            # Lấy dữ liệu BCTC — thử yearly trước, quarterly nếu yearly < 2 hàng
            def _fetch(period):
                try:
                    return financial_ratio(symbol, period, True)
                except:
                    return None

            df = _fetch('yearly')
            if df is None or len(df) < 2:
                df_q = _fetch('quarterly')
                if df_q is not None and len(df_q) >= 2:
                    df = df_q

            if df is None or df.empty:
                raise ValueError("Không tìm thấy dữ liệu cơ bản")

            # ── Normalize column names (vnstock khác phiên bản trả tên cột khác) ──
            col_map = {c.lower().replace(' ', '').replace('_', '').replace('/', ''): c
                       for c in df.columns}

            def _col(*keys):
                for k in keys:
                    if k.lower().replace('_', '') in col_map:
                        return col_map[k.lower().replace('_', '')]
                return None

            eps_col  = _col('earningPerShare', 'eps', 'epsbasic', 'EPS')
            pe_col   = _col('priceToEarning', 'pe', 'priceearning', 'PE')
            pb_col   = _col('priceToBook', 'pb', 'pricebook', 'PB')
            roe_col  = _col('roe', 'ROE')
            eps_chg_col = _col('epsChange', 'epschange')   # Cột thay đổi EPS YoY trực tiếp

            latest  = df.iloc[0]

            def get_safe(val, default):
                try:
                    vf = float(val)
                    return default if pd.isna(vf) else vf
                except:
                    return default

            pe_actual  = get_safe(latest.get(pe_col),  0.0) if pe_col else 0.0
            pb         = get_safe(latest.get(pb_col),  1.5) if pb_col else 1.5
            roe        = get_safe(latest.get(roe_col), 0.15) if roe_col else 0.15
            eps_actual = get_safe(latest.get(eps_col),  0.0) if eps_col else 0.0
            # Normalize EPS: vnstock đôi khi trả đơn vị nghìn đồng thay vì đồng
            if 0 < eps_actual < 50:
                eps_actual *= 1000

            # ── YoY Growth: ưu tiên epsChange trực tiếp, fallback tự tính ──
            yoy_growth = 0.0
            if eps_chg_col:
                # vnstock trả trực tiếp % thay đổi YoY (dạng 0.25 = 25%)
                raw_chg = get_safe(latest.get(eps_chg_col), None)
                if raw_chg is not None:
                    # Normalize: nếu > 5 thì đang là %, chia 100
                    yoy_growth = raw_chg / 100 if abs(raw_chg) > 5 else raw_chg

            if yoy_growth == 0.0:
                # Tự tính từ income_statement LNST thực (chính xác nhất)
                try:
                    from vnstock import income_statement as _is
                    is_df = _is(symbol, 'yearly', True)
                    if is_df is not None and len(is_df) >= 2:
                        # Tìm cột LNST (postTaxProfit / netProfit)
                        is_col_map = {c.lower().replace(' ','').replace('_','').replace('/','').replace('-',''): c
                                      for c in is_df.columns}
                        lnst_key = None
                        for k in ['postTaxProfit','netProfit','lnst','netincome','aftertaxprofit']:
                            if k in is_col_map:
                                lnst_key = is_col_map[k]
                                break
                        if lnst_key:
                            lnst_now  = get_safe(is_df.iloc[0].get(lnst_key), 0.0)
                            lnst_prev = get_safe(is_df.iloc[1].get(lnst_key), 0.0)
                            if lnst_prev > 0 and lnst_now > 0:
                                yoy_growth = (lnst_now - lnst_prev) / lnst_prev
                except Exception as ye:
                    print(f"[{symbol}] income_statement YoY error: {ye}")

            if yoy_growth == 0.0 and eps_col and len(df) >= 2:
                # Fallback: tính từ EPS financial_ratio
                # Với quarterly: so cùng kỳ năm trước (4 quý trước), không so quý liền kề
                prev_idx = min(4, len(df) - 1)   # 4 quý trước = cùng kỳ năm trước
                eps_prev = get_safe(df.iloc[prev_idx].get(eps_col), 0.0)
                if 0 < eps_prev < 50:
                    eps_prev *= 1000
                if eps_prev > 0 and eps_actual > 0:
                    yoy_growth = (eps_actual - eps_prev) / eps_prev

            industry_pe = FundamentalService._get_industry_pe(symbol)
            pe_eval     = FundamentalService._pe_label(pe_actual if pe_actual > 0 else industry_pe, industry_pe)

            if eps_actual > 0:
                fair_value = FundamentalService._round_to_tick(eps_actual * industry_pe)
            else:
                fair_value = FundamentalService._round_to_tick(current_price * 1.15)

            upside    = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0
            mos_zones = FundamentalService._build_mos_zones(fair_value, current_price)

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
                },
                "status": "Proxy 🟡"
            }


fundamental_service = FundamentalService()
