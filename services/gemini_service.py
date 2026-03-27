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
Bạn là Giám đốc Phân tích Định lượng (AstraAI Signals V6.0 Alpha).
Hãy đọc kỹ kết quả Dữ Liệu Thô (Raw Data) của cổ phiếu {symbol} dưới đây:

{json.dumps(layers_data, ensure_ascii=False)}

YÊU CẦU KHẮC NGHIỆT (STRICT CONCISENESS RULE):
TUYỆT ĐỐI KHÔNG viết đoạn văn dài. Bạn PHẢI viêt dạng GẠCH ĐẦU DÒNG (Bullet Points) cho từng tầng phân tích.
Mỗi tầng CHỈ ĐƯỢC TỐI ĐA 2 GẠCH ĐẦU DÒNG. Mỗi dòng DƯỚI 20 TỪ. Cấm giải thích dông dài. CHỈ CHÁNH VÀO KẾT LUẬN (Tốt/Xấu/Hành Động).

1. Phân tích Kỹ thuật: Xu hướng chính? Tín hiệu MACD/RSI Tốt hay Xấu?
2. Dòng tiền: Cá mập đang gom hay xả? Khối ngoại mua hay bán ròng?
3. Cơ bản: P/E đắt hay rẻ so với trung bình?
4. Vĩ mô: Trích XUẤT ĐÚNG 1 TIN NÓNG NHẤT trong Data Tầng 4. Kết luận tin này TÍCH CỰC hay TIÊU CỰC.
5. Tin đồn/Sự kiện: Đánh giá tâm lý FOMO/FUD hiện hữu từ Data Tầng 5.
6. Intraday: Lực mua/bán chủ động trong ngày.
7. Khuyến nghị (Recommendation): CHỈ GHI ĐÚNG 1 CỤM TỪ (MUA MẠNH / NẮM GIỮ / BÁN CHẶN LÃI / QUAN SÁT) kèm 1 lý do ngắn.

BẮT BUỘC ĐÁNH GIÁ CHỈ SỐ V4_METRICS:
- "compression_score": Số thập phân 0-100 đo độ nén giá.
- "whale_style": 1 Cụm từ DUY NHẤT (VD: "Gom Hàng Tích Lũy", "Kéo Xả Phân Phối", "Lái Đảo Hàng", "Siết Nền").
- "hunting_zones": Mảng chứa [Giá Đáy Hỗ Trợ, Giá Đỉnh Kháng Cự] gần nhất.

Đầu ra DUY NHẤT LÀ JSON (Các giá trị dưới là VÍ DỤ CẤU TRÚC):
{{
  "tech_text": "...",
  "sm_text": "...",
  "fundamental_text": "...",
  "macro_text": "...",
  "news_text": "...",
  "intraday_text": "...",
  "recommendation": "Tóm tắt hành động...",
  "v4_metrics": {{
      "compression_score": 62,
      "whale_style": "Đội Lái Đầu Cơ",
      "hunting_zones": [15.2, 17.0]
  }}
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

    def synthesize_market_overview(self, data: dict) -> str:
        """
        Layer 8: Toàn cảnh Thị trường. Phân tích Dòng tiền Luân chuyển.
        """
        if not self.model:
            return "Hệ thống AI Đang Tắt (Thiếu API Key)."
        
        prompt = f"""
Bạn là Tổng Tư Lệnh của AstraAI Signals V6.
Dựa vào số liệu Tòa Cảnh (VNINDEX & Dòng Nhóm Ngành) sau đây:
{json.dumps(data, ensure_ascii=False)}

YÊU CẦU KHẮC NGHIỆT (DƯỚI 50 TỪ):
Viết đúng 1 đoạn văn siêu ngắn gọn, đi thẳng vào kết luận. Lựa lời văn sắc bén, lạnh lùng của dân Trading.
1. VNINDEX hiện tại đang Tích lũy, FOMO hay Phân phối?
2. Dòng tiền (Khối lượng) đang CHẢY MẠNH NHẤT MUA RÒNG vào Ngành nào (Dựa vào số dương cao nhất của sector_flow) và RÚT ĐÁY KHỎI Ngành nào?
Tuyệt đối không giải thích dông dài. KHÔNG VIẾT DẠNG JSON. Viết dạng Text bình thường.
        """
        try:
            return self.model.generate_content(prompt).text.strip()
        except Exception as e:
            return f"Lỗi AI: Nguồn cấp nghẽn ({e})."

gemini_service = GeminiService()
