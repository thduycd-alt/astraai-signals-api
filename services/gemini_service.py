import os
import google.generativeai as genai
import json

class GeminiService:
    def __init__(self):
        # Hệ thống trích xuất Khóa API bằng Biến Môi trường (Bắt buộc Khai báo trên Render)
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    def synthesize_analysis(self, symbol: str, layers_data: dict) -> dict:
        """
        Layer 7 (Tự Hấp Thụ V3): Gemini viết TOÀN BỘ 6 TẦNG.
        """
        if not self.model:
            return {}

        prompt = f"""
Bạn là Giám đốc Phân tích Định lượng (AstraAI Signals V3 Enterprise).
Hãy đọc kỹ kết quả Dữ Liệu Thô (Raw Data) của cổ phiếu {symbol} dưới đây:

{json.dumps(layers_data, ensure_ascii=False)}

YÊU CẦU BẮT BUỘC:
Dựa vào data thô ở trên, bạn phải tự tay VIẾT LỜI BÌNH CHUYÊN SÂU bằng Tiếng Việt cho TỪNG TẦNG MỘT (Khoảng 50-70 chữ mỗi tầng). Bố cục chuyên nghiệp như Quỹ phòng hộ (Hedge Fund).
1. Phân tích Kỹ thuật: Phải nhắc đến Xu hướng, SMC, Breakout/Pullback, MACD/RSI.
2. Dòng tiền (Smart Money): Phải nhắc đến Lực mua/bán, Order lớn/nhỏ, Gom bao nhiêu triệu qua 15 phiên, Khối ngoại.
3. Cơ bản: Đánh giá nhanh về lợi nhuận, định giá P/E.
4. Vĩ mô: Trích dẫn tin vĩ mô CafeF, móc nối với Tỷ giá DXY, FED, Lãi suất VN.
5. Tin đồn: Đọc các tin CafeF được cào về và đánh giá tâm lý Fomo/Fud.
6. Intraday: Lệnh trong ngày.
7. Cuối cùng, tóm tắt Lời khuyên cuối.

Đầu ra DUY NHẤT LÀ ĐỊNH DẠNG JSON SAU (Không chứa text dài dòng bên ngoài):
{{
  "tech_text": "...",
  "sm_text": "...",
  "fundamental_text": "...",
  "macro_text": "...",
  "news_text": "...",
  "intraday_text": "...",
  "recommendation": "Tóm tắt hành động 50 chữ...",
  "action": "BUY / STRONG_BUY / HOLD / SELL / STRONG_SELL (Tùy theo kết luận của bạn)"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Lọc bớt block text ```json
            result_text = response.text.strip()
            import re
            
            # Tương thích với việc Model hay nói nhiều "Dạ phần tích đây ạ: { ... }"
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                result_json = json.loads(clean_json)
                result_json["disclaimer"] = "Báo cáo Tự động tạo bởi Gemini 2.5 Flash AI kết hợp AstraAI V3 Enterprise Algorithms."
                return result_json
            else:
                print("Gemini Output Not Found JSON Data")
                return {}
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return {}

gemini_service = GeminiService()
