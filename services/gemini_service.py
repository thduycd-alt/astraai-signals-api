import os
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        # Hệ thống trích xuất Khóa API bằng Biến Môi trường, fallback sang Key Chủ Tịch
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyDZ0ZfwEUu35_oT4IXJQz4E-ioSoqbh71Y")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Khởi tạo siêu mẫu Gemini 2.5 Flash mới nhất
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    def synthesize_analysis(self, symbol: str, layers_data: dict) -> dict:
        """
        Layer 7 (Tự Hấp Thụ): Bọc gói Dữ liệu 6 Tầng quăng hết cho Gemini 2.5 đọc hiểu.
        """
        if not self.model:
            return {
                "final_score": 50,
                "recommendation": "[Thiếu Gemini API Key] Dữ liệu chưa thể tổng hợp. Yêu cầu nhập Key.",
                "action": "ERROR"
            }

        # Tạo chuỗi cấu trúc Json/Text đơn giản để Gemini dễ tiếp thu
        prompt = f"""
Bạn là siêu chuyên gia tài chính Vua (AstraAI Signals).
Hãy đọc kỹ kết quả phân tích hệ thống tự động bóc tách của cổ phiếu {symbol} dựa trên 6 Lớp Phân Tích dưới đây:

{layers_data}

Nhiệm vụ của bạn:
1. Đánh giá Mức độ rủi ro (Kết hợp Vĩ mô, Sóng Ngắn và Dòng tiền).
2. Viết ra XÁC ĐÁNG MỘT (1) ĐOẠN VĂN DUY NHẤT khoảng 80-100 chữ tóm tắt Khuyến Nghị Mua/Bán (Chốt hạ) cuối cùng. Văn phong cực kỳ nghiêm túc, quyết liệt, nhiều Thuật ngữ ngành chứng khoán VN (như Rũ vỏ, Phân phối, Gom hàng, Lái, Cá mập...). Chỉ viết 1 đoạn rành mạch, không xuống dòng.
3. Cho điểm số chung từ 0 đến 100.

Chỉ trả về ĐÚNG MỘT JSON với định dạng sau (Không chứa dấu block markdown):
{{
  "final_score": (số nguyên từ 0-100),
  "recommendation": "(đoạn văn khuyến nghị 80 chữ của bạn)",
  "action": "(BUY / STRONG_BUY / HOLD / SELL / STRONG_SELL theo điểm số trên)"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Lọc bớt block text ```json
            result_text = response.text.strip().replace("```json", "").replace("```", "")
            
            import json
            result_json = json.loads(result_text)
            result_json["disclaimer"] = "Khuyến nghị độc quyền tạo ra bởi Gemini 2.5 Flash AI kết hợp AstraAI Algorithms."
            return result_json

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return {
                "final_score": 0,
                "recommendation": f"Lỗi gọi Gemini 2.5: {str(e)}",
                "action": "ERROR"
            }

gemini_service = GeminiService()
