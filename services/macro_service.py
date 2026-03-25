import requests
from bs4 import BeautifulSoup

class MacroService:
    """
    Layer 4: Vĩ mô (10%)
    Theo dõi DXY, Lãi suất SBV, CPI, và quét thông tư chính phủ.
    """

    @staticmethod
    def analyze(symbol: str) -> dict:
        try:
            # Module này sử dụng Celery Background Workers để crawl chinhphu.vn định kỳ
            # Trong production, dữ liệu crawl sẽ được chọc từ PostgreSQL.
            
            # Mock data response cho MVP 
            mock_sbv_rate = "Ngân hàng nhà nước bơm ròng thanh khoản OMO"
            mock_dxy = 104.2 # Chỉ số Dollar Index
            mock_policy = "Thủ tướng ký quyết định thúc đẩy giải ngân đầu tư công"
            
            # Khung tính điểm vĩ mô (0-100)
            score = 50
            if "bơm ròng" in mock_sbv_rate.lower() or "giảm lãi suất" in mock_sbv_rate.lower():
                score += 20 # Tiền rẻ = Mua
                
            if mock_dxy < 105: # Tỷ giá bớt sức ép, khối ngoại ngừng bán ròng
                score += 15
            else:
                score -= 15
                
            if "thúc đẩy" in mock_policy or "gỡ khó" in mock_policy:
                score += 10
                
            return {
                "score": max(0, min(100, score)),
                "metrics": {
                    "SBV_Action": mock_sbv_rate,
                    "DXY_Index": mock_dxy,
                    "Gov_Policy": mock_policy
                },
                "status": "Positive (Hỗ trợ thị trường)" if score > 60 else "Negative (Rủi ro suy thoái)"
            }
        except Exception as e:
            print(f"Macro Analysis Error: {e}")
            return {"error": str(e), "score": 50}

macro_service = MacroService()
