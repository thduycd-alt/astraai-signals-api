import requests
from bs4 import BeautifulSoup

class NewsRumorService:
    """
    Layer 5: Tin tức, Rumor & Lập trường KOL (Trọng số 15%)
    Dùng Web Scraper chọc vào HTML của CafeF để đọc thẳng 5 tin mới nhất của Cổ phiếu.
    """

    @staticmethod
    def analyze(symbol: str, custom_kols: list = None) -> dict:
        try:
            headlines = []
            sentiment_score = 50
            
            # --- 1. BẮT ĐẦU CÀO DỮ LIỆU TỪ CAFEF ---
            # Sử dụng API chìm của CafeF trả về HTML list tin tức
            url = f"https://s.cafef.vn/Ajax/Events_RelatedNews_New.aspx?symbol={symbol}&startIndex=0&pageSize=5"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Trích xuất tiêu đề (nằm trong the <a> có class 'docnhanhTitle')
                links = soup.find_all('a', class_='docnhanhTitle')
                for link in links:
                    title = link.text.strip()
                    if title:
                        headlines.append(title)
            
            if not headlines:
                headlines = [f"Chưa có tin tức nổi bật nào về {symbol} trên diện rộng."]
            
            # --- 2. THUẬT TOÁN CHẤM ĐIỂM (NLP ĐƠN GIẢN) ---
            # Tạo bộ từ khóa để quét cảm xúc tiêu đề
            positive_words = ['lãi', 'tăng', 'khủng', 'vượt', 'hợp tác', 'ký kết', 'cổ tức', 'chấp thuận', 'khởi sắc', 'kỷ lục']
            negative_words = ['lỗ', 'giảm', 'bán', 'tháo', 'bắt', 'khởi tố', 'hủy', 'đỉnh', 'cảnh báo', 'rủi ro', 'lao dốc']
            
            pos_count = 0
            neg_count = 0
            
            for hl in headlines:
                text_lower = hl.lower()
                for w in positive_words:
                    if w in text_lower: pos_count += 1
                for w in negative_words:
                    if w in text_lower: neg_count += 1
            
            bias = (pos_count - neg_count) * 10
            sentiment_score = max(0, min(100, 50 + bias))

            return {
                "score": sentiment_score,
                "latest_headlines": headlines,
                "status": "Tích cực (Tin Tốt Tràn Ngập)" if sentiment_score > 60 else ("Tiêu cực (Ngập lụt tin FUD)" if sentiment_score < 40 else "Trung Lập")
            }
            
        except Exception as e:
            print(f"News Scraper Error: {e}")
            return {
                "score": 50,
                "latest_headlines": ["Lỗi kết nối tới Máy chủ lấy tin CafeF."],
                "status": "Lỗi cào dữ liệu",
                "error": str(e)
            }

news_rumor_service = NewsRumorService()
