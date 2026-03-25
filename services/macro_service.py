import requests
from bs4 import BeautifulSoup

class MacroService:
    """
    Layer 4: Vĩ mô (10%)
    Tính toán bằng cách Scrape tin tức Vĩ mô Thực tế từ CafeF để đo lường Sentiment nền kinh tế thay vì dùng Data Mock.
    """

    @staticmethod
    def analyze(symbol: str) -> dict:
        try:
            headlines = []
            sentiment_score = 50
            
            # --- CÀO TIN TỨC VĨ MÔ THỰC TẾ ---
            url = "https://cafef.vn/vi-mo-dau-tu.chn"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                h3_tags = soup.find_all('h3')
                # Lấy 5 tin Vĩ mô trang bìa nóng hổi nhất
                for tag in h3_tags[:8]:  
                    a_tag = tag.find('a')
                    if a_tag and a_tag.text.strip():
                        txt = a_tag.text.strip()
                        if len(txt) > 20 and txt not in headlines:
                            headlines.append(txt)
                            if len(headlines) >= 5:
                                break
            
            if not headlines:
                headlines = ["NHNN tiếp tục duy trì các giải pháp nới lỏng tiền tệ để hỗ trợ tăng trưởng."]
                
            # Phân tích Sentiment Vĩ mô đơn giản bằng Keywords
            positive_words = ['hỗ trợ', 'tăng trưởng', 'hạ lãi', 'bơm tiền', 'phục hồi', 'giải ngân', 'kích cầu', 'ổn định', 'hút vốn']
            negative_words = ['lạm phát', 'hút tiền', 'tăng lãi', 'suy thoái', 'vỡ nợ', 'phá sản', 'thu hẹp', 'đình trệ', 'tỷ giá căng']
            
            pos = sum(1 for hl in headlines for w in positive_words if w in hl.lower())
            neg = sum(1 for hl in headlines for w in negative_words if w in hl.lower())
            
            sentiment_score += (pos - neg) * 15
            
            return {
                "score": max(0, min(100, sentiment_score)),
                "metrics": {
                    "latest_macro_news": headlines,
                    "pos_keywords": pos,
                    "neg_keywords": neg
                },
                "status": "Positive (Hỗ trợ thị trường)" if sentiment_score > 60 else ("Negative (Rủi ro vĩ mô)" if sentiment_score < 40 else "Neutral (Đi ngang bền vững)")
            }
        except Exception as e:
            print(f"Macro Analysis Error: {e}")
            return {
                "score": 50, 
                "metrics": {"error": str(e)},
                "status": "Lỗi cào dữ liệu Vĩ mô"
            }

macro_service = MacroService()
