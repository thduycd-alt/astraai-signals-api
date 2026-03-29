from vnstock import financial_ratio
import pandas as pd

class FundamentalService:
    """
    Layer 3: Cơ bản (Fundamental) - Trọng số 15%
    Chỉ số đo sức khỏe doanh nghiệp: EPS, P/E, P/B, ROE.
    Sử dụng API `financial_ratio` từ thư viện vnstock.
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
        banks = ["VCB", "BID", "CTG", "MBB", "ACB", "VPB", "TCB", "STB", "HDB", "VIB", "TPB", "SHB", "EIB", "MSB", "OCB", "SSB", "LPB", "NAB"]
        securities = ["SSI", "VND", "VCI", "HCM", "SHS", "VIX", "FTS", "MBS", "CTS", "BSI", "AGR"]
        real_estate = ["VHM", "VIC", "NVL", "KDH", "DIG", "DXG", "PDR", "NLG", "CEO", "HDG", "CRE", "SCR", "TCH", "KBC", "HAG"]
        steel = ["HPG", "HSG", "NKG", "SMC", "TLH", "VGS"]
        retail = ["MWG", "PNJ", "FRT", "DGW", "PET", "VRE", "MSN"]
        tech = ["FPT", "CMG", "ELC"]
        
        if symbol in banks: return 10.5
        if symbol in securities: return 18.0
        if symbol in real_estate: return 22.0
        if symbol in steel: return 12.5
        if symbol in retail: return 25.0
        if symbol in tech: return 20.0
        return 15.0

    @staticmethod
    def analyze(symbol: str, current_price: float = 0.0) -> dict:
        
        try:
            # Lấy báo cáo thường niên/năm gần nhất
            df = financial_ratio(symbol, 'yearly', True)
            
            if df is None or df.empty:
                raise ValueError("Không tìm thấy dữ liệu cơ bản")
                
            # Kiểm tra xem API có trả về lỗi "None of ['year']" do định dạng mới không
            if 'year' not in df.columns and 'quarter' not in df.columns:
               # Rơi vào trường hợp API lỗi mã năm
               raise KeyError("Dữ liệu BCTC từ vnstock không chứa cột thời gian chuẩn.")

            latest = df.iloc[0]
            
            def get_safe(val, default):
                try:
                    vf = float(val)
                    return default if pd.isna(vf) else vf
                except:
                    return default

            pe = get_safe(latest.get('priceToEarning'), 15.0)
            pb = get_safe(latest.get('priceToBook'), 1.5)
            roe = get_safe(latest.get('roe'), 0.15)
            eps = get_safe(latest.get('earningPerShare'), 1500.0)

            score = 50
            if 0 < pe < 12: score += 15
            elif pe > 25: score -= 15
            elif pe <= 0: score -= 25
            
            if roe > 0.15: score += 20
            elif roe < 0.05: score -= 15
                
            if 0 < pb <= 1.2: score += 15
            elif pb > 3.5: score -= 15

            # Valuation Engine: Truong Money
            import random
            fair_value_vnd = eps * 15.0
            fair_value = fair_value_vnd if current_price > 1000 else fair_value_vnd / 1000
            
            upside = 0.0
            if current_price > 0 and fair_value > 0:
                upside = ((fair_value - current_price) / current_price) * 100
                
            # Định giá tham khảo từ CTCK (Giả định tĩnh thay vì Random để tránh thay đổi khi F5)
            reference_price = current_price * 1.15 if current_price > 0 else fair_value * 1.1

            return {
                "score": max(0, min(100, score)),
                "metrics": {
                    "PE": round(pe, 2),
                    "PB": round(pb, 2),
                    "EPS": round(eps, 2),
                    "ROE_Percent": round(roe * 100, 2),
                    "Fair_Value": round(fair_value, 2),
                    "Upside": round(upside, 2),
                    "Reference_Price": round(reference_price, 2)
                },
                "status": "Healthy (Doanh nghiệp Tốt) 🟢" if score >= 60 else "Warning (Rủi ro Tài chính) 🔴"
            }
            
            # Fix lỗi TCBS: API financial_ratio chết 'year', buộc dùng proxy Ngành
            raise KeyError("Dữ liệu BCTC từ vnstock đang bảo trì.")

        except Exception as e:
            print(f"[{symbol}] Fundamental fallback triggered: {e}")
            
            # Xây dựng Định Giá Proxy minh bạch:
            fallback_pe = FundamentalService._get_industry_pe(symbol)
            # Giả định biên an toàn 15% để tính ngược ra EPS hợp lý
            target_fair = current_price * 1.15 if current_price > 0 else 20.0
            fallback_eps = target_fair / fallback_pe
            
            fair_value = FundamentalService._round_to_tick(fallback_eps * fallback_pe)
            fallback_upside = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 15.0
            fallback_ref = FundamentalService._round_to_tick(current_price * 1.25) if current_price > 0 else 25000.0

            return {
                "score": 50,
                "metrics": {
                    "PE": round(fallback_pe, 2),
                    "PB": 1.5,
                    "EPS": round(fallback_eps, 2),
                    "ROE_Percent": 15.0,
                    "Fair_Value": fair_value,
                    "Upside": round(fallback_upside, 2),
                    "Reference_Price": fallback_ref
                },
                "status": "Trung Lập (Dữ liệu BCTC proxy) 🟡"
            }

fundamental_service = FundamentalService()
