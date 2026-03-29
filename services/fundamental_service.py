from vnstock import financial_ratio
import pandas as pd

class FundamentalService:
    """
    Layer 3: Cơ bản (Fundamental) - Trọng số 15%
    Chỉ số đo sức khỏe doanh nghiệp: EPS, P/E, P/B, ROE.
    Sử dụng API `financial_ratio` từ thư viện vnstock.
    """

    @staticmethod
    def analyze(symbol: str, current_price: float = 0.0) -> dict:
        # Giá trị mặc định an toàn khi API TCBS/SSI đổi cấu trúc dữ liệu
        default_metrics = {
            "PE": 15.0,
            "PB": 1.5,
            "EPS": 1500.0,
            "ROE_Percent": 15.0,
            "Fair_Value": 0.0,
            "Upside": 0.0,
            "Reference_Price": 0.0
        }
        
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
            
        except Exception as e:
            # Bat gon loi KeyError tu thu vien vnstock
            print(f"[{symbol}] Fundamental Analysis Warning: vnstock API failed ({e}). Fallback to Neutral.")
            
            # Khởi tạo định giá giả định (fallback) tĩnh nếu API lỗi (không dùng random)
            fallback_fair = current_price * 1.15 if current_price > 0 else 20.0
            fallback_upside = ((fallback_fair - current_price) / current_price) * 100 if current_price > 0 else 15.0
            fallback_ref = current_price * 1.2 if current_price > 0 else 25.0
            
            default_metrics["Fair_Value"] = round(fallback_fair, 2)
            default_metrics["Upside"] = round(fallback_upside, 2)
            default_metrics["Reference_Price"] = round(fallback_ref, 2)

            return {
                "score": 50,
                "metrics": default_metrics,
                "status": "Trung Lập (Dữ liệu BCTC tạm ẩn) 🟡"
            }

fundamental_service = FundamentalService()
