from vnstock import financial_ratio
import pandas as pd

class FundamentalService:
    """
    Layer 3: Cơ bản (Fundamental) - Trọng số 15%
    Chỉ số đo sức khỏe doanh nghiệp: EPS, P/E, P/B, ROE.
    Sử dụng API `financial_ratio` từ thư viện vnstock.
    """

    @staticmethod
    def analyze(symbol: str) -> dict:
        # Giá trị mặc định an toàn khi API TCBS/SSI đổi cấu trúc dữ liệu
        default_metrics = {
            "PE": 15.0,
            "PB": 1.5,
            "EPS": 1500.0,
            "ROE_Percent": 15.0
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
            
            pe = float(latest.get('priceToEarning', 15.0) or 15.0)
            pb = float(latest.get('priceToBook', 1.5) or 1.5)
            roe = float(latest.get('roe', 0.15) or 0.15)
            eps = float(latest.get('earningPerShare', 1500) or 1500)

            score = 50
            if 0 < pe < 12: score += 15
            elif pe > 25: score -= 15
            elif pe <= 0: score -= 25
            
            if roe > 0.15: score += 20
            elif roe < 0.05: score -= 15
                
            if 0 < pb <= 1.2: score += 15
            elif pb > 3.5: score -= 15

            return {
                "score": max(0, min(100, score)),
                "metrics": {
                    "PE": round(pe, 2),
                    "PB": round(pb, 2),
                    "EPS": round(eps, 2),
                    "ROE_Percent": round(roe * 100, 2)
                },
                "status": "Healthy (Doanh nghiệp Tốt) 🟢" if score >= 60 else "Warning (Rủi ro Tài chính) 🔴"
            }
            
        except Exception as e:
            # Bắt gọn lỗi KeyError từ thư viện vnstock do nhà mạng đổi cấu trúc API
            print(f"[{symbol}] Fundamental Analysis Warning: Nguồn API vnstock bị lỗi ({e}). Fallback to Neutral.")
            return {
                "score": 50,
                "metrics": default_metrics,
                "status": "Trung Lập (Dữ liệu BCTC tạm ẩn) 🟡"
            }

fundamental_service = FundamentalService()
