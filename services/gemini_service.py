import os
import google.generativeai as genai
import json
import re

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
        Layer 7 (Tự Hấp Thụ V3): Gemini viết TOÀN BỘ BẢNG TẦM SOÁT 6 BƯỚC VÀ 15 TIÊU CHÍ.
        """
        if not self.model:
            return {}

        # Đọc tài liệu tầm soát từ các file PDF đã upload
        training_knowledge = ""
        symbol_specific_knowledge = ""
        try:
            kb_path = os.path.join(os.path.dirname(__file__), '..', 'pdf_dump_utf8.txt')
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    training_knowledge = f.read()

                # Trích riêng phần báo cáo của symbol hiện tại (nếu có)
                import re
                pattern = rf'=== TÀI LIỆU \d+:.* {re.escape(symbol)}[^=]*===\n(.+?)(?:={3,}|\Z)'
                match = re.search(pattern, training_knowledge, re.DOTALL | re.IGNORECASE)
                if match:
                    symbol_specific_knowledge = match.group(0).strip()
        except Exception as e:
            print(f"[GeminiService] PDF load error: {e}")

        prompt = f"""
=== [DANH TÍNH & TƯ DUY CỐT LÕI] ===
Bạn là Chuyên gia Phân tích Tầm Soát theo Phương pháp Trường Money.
Bạn KHÔNG phân tích cảm tính. Bạn KHÔNG học vẹt. Bạn có BỘ NÃO NGUYÊN TẮC sau đây:

--- NGUYÊN TẮC I: PHÂN LOẠI DOANH NGHIỆP TRƯỚC KHI ĐỊNH GIÁ ---
Bước 1 bắt buộc: Phân loại cổ phiếu vào 1 trong 4 nhóm dựa vào dữ liệu:
• NHÓM A - PHỤC HỒI: BĐS có pipeline bàn giao lớn, chu kỳ ngành đang lên, lợi nhuận trailing thấp/âm nhưng forward cao.
  → Fwd EPS = Ước từ pipeline + kế hoạch công ty (có thể gấp 3-10x trailing)
  → P/E áp dụng: 15-22x (BĐS phục hồi), 10-15x (chu kỳ lên)
• NHÓM B - TĂNG TRƯỞNG ĐỀU: Ngân hàng, Bán lẻ, Tiêu dùng, lợi nhuận ổn định YoY+.
  → Fwd EPS = Trailing × (1 + YoY%) × 1.1 (buffer tăng trưởng nhẹ)
  → P/E áp dụng: NH 7-10x, Bán lẻ 12-18x, Tech 15-22x
• NHÓM C - KHÓ KHĂN: Lợi nhuận âm, nợ vay tăng, dòng tiền âm liên tục.
  → Fwd EPS = Trailing × 0.8 (bảo thủ)
  → P/E áp dụng: 6-10x (rủi ro cao)
• NHÓM D - CHU KỲ: Thép, Phân bón, Dầu khí — biến động theo giá hàng hóa.
  → Fwd EPS = Ước theo chu kỳ ngành
  → P/E áp dụng: 6-9x đỉnh chu kỳ, 12-15x đáy chu kỳ

--- NGUYÊN TẮC II: FORWARD EPS PHẢI HỢP LÝ KINH TẾ ---
• NẾU trailing EPS rất thấp/nhỏ so với giá thị trường (P/E trailing > 30x), KHÔNG dùng trailing làm base.
  → Hãy ước lại EPS từ: ROE × Book value/share, hoặc từ LNST kế hoạch năm, hoặc từ pipeline.
• EPS Fwd tính = Trailing EPS × (1 + eps_growth_forecast_pct/100)
• Kết quả Fair Value = Fwd EPS × target_pe phải nằm trong vùng ±50% giá thị trường để có ý nghĩa.
  → Nếu Fair Value tính ra < 30% giá thị trường: PHẢI xem lại EPS. Có thể trailing bị bóp méo.
  → Nếu Fair Value tính ra > 200% giá thị trường: PHẢI giảm P/E xuống mức thực tế ngành.

--- NGUYÊN TẮC III: CHẤM ĐIỂM 15 TIÊU CHÍ LÀ TƯ DUY, KHÔNG PHẢI ĐỌC THUỘC ---
Mỗi tiêu chí: suy luận "Tại sao?" dựa trên dữ liệu. Lý luận < 12 từ, sắc bén.
Điểm 0-3: 0=Không đáp ứng, 1=Yếu, 1.5=Dưới trung bình, 2=Trung bình, 2.5=Tốt, 3=Xuất sắc.

=== [TÀI LIỆU MẪU ĐỂ ĐỌC HIỂU VĂN PHONG & PHONG CÁCH PHÂN TÍCH] ===
=== [TÀI LIỆU MẪU ĐỂ ĐỌC HIỂU VĂN PHONG & PHONG CÁCH PHÂN TÍCH] ===
{f'''
>>> ƯU TIÊN CAO NHẤT: BÁO CÁO PHÂN TÍCH RIÊNG CHO {symbol} TỪ VIỆN CỔ PHIẾU <<<
Nếu dưới đây có báo cáo phân tích {symbol}, hãy sử dụng các số liệu, luận điểm và nhận định trong đó làm CĂN CỨ CHÍNH để ước Fwd EPS và target_pe. KHÔNG bỏ qua bất kỳ thông tin nào.

{symbol_specific_knowledge}

>>> CÁC BÁO CÁO KHÁC (học phong cách, không copy số liệu) <<<
{training_knowledge[:5000]}... [và các báo cáo còn lại]
''' if training_knowledge else 'Không có tài liệu mẫu.'}

=== [DỮ LIỆU THỰC TẾ CỔ PHIẾU {symbol} CẦN PHÂN TÍCH] ===
{json.dumps(layers_data, ensure_ascii=False)}

=== [NHIỆM VỤ] ===
BƯỚC 1: Phân loại {symbol} vào NHÓM A/B/C/D theo NGUYÊN TẮC I.
BƯỚC 2: Tính Fwd EPS và target_pe theo đúng nguyên tắc nhóm tương ứng.
BƯỚC 3: Kiểm tra Fair Value = Fwd EPS × target_pe có hợp lý kinh tế không (NGUYÊN TẮC II).
BƯỚC 4: Chấm điểm 15 tiêu chí (NGUYÊN TẮC III).
BƯỚC 5: Trả về JSON (KHÔNG viết gì ngoài JSON):

{{
  "criteria_list": [
    {{"id": 1, "name": "Lợi nhuận từ HĐKD cốt lõi > 90%", "score": 2.5, "reason": "Lý luận < 12 từ"}},
    {{"id": 2, "name": "Lợi nhuận có tính kế thừa", "score": 2.0, "reason": "..."}},
    {{"id": 3, "name": "Đầu vào và đầu ra có cải thiện", "score": 2.5, "reason": "..."}},
    {{"id": 4, "name": "Tiềm năng thị trường tiêu thụ tương lai", "score": 2.0, "reason": "..."}},
    {{"id": 5, "name": "Lợi nhuận bất thường < 10%", "score": 2.5, "reason": "..."}},
    {{"id": 6, "name": "Chất lượng ban lãnh đạo", "score": 2.0, "reason": "..."}},
    {{"id": 7, "name": "Tính minh bạch của doanh nghiệp", "score": 2.5, "reason": "..."}},
    {{"id": 8, "name": "Lợi thế thương mại trong ngành", "score": 2.5, "reason": "..."}},
    {{"id": 9, "name": "Năng lực sản xuất trong tương lai", "score": 2.5, "reason": "..."}},
    {{"id": 10, "name": "Sản phẩm mới", "score": 1.5, "reason": "..."}},
    {{"id": 11, "name": "Cổ đông lớn có tác động", "score": 2.0, "reason": "..."}},
    {{"id": 12, "name": "Phát minh/sáng chế/cải tiến mới", "score": 1.5, "reason": "..."}},
    {{"id": 13, "name": "Biên lợi nhuận cải thiện", "score": 2.0, "reason": "..."}},
    {{"id": 14, "name": "Doanh thu & lợi nhuận lõi tăng trưởng", "score": 2.5, "reason": "..."}},
    {{"id": 15, "name": "Vị thế ngành", "score": 2.5, "reason": "..."}}
  ],
  "total_score": 32.5,
  "max_score": 45,
  "quality_rating": "KHÁ",
  "eps_growth_forecast_pct": 350.0,
  "target_pe": 18.0,
  "recommendation": "TÍCH LŨY",
  "action": "BUY",
  "v4_metrics": {{
      "compression_score": 62,
      "whale_style": "Gom Hàng Tích Lũy",
      "hunting_zones": [13500, 15500]
  }}
}}
"""

        
        try:
            # JSON Mode: Ép output JSON cứng, loại bỏ hoàn toàn lỗi parse
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            result_json = json.loads(response.text)
            result_json["disclaimer"] = "Báo cáo Tự động tạo bởi Gemini 2.5 Flash AI kết hợp AstraAI V3 Enterprise Algorithms."
            return result_json
        except Exception as e:
            print(f"Gemini API Error: {e}")
            # Fallback: thử parse regex nếu JSON mode lỗi
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except:
                pass
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

YÊU CẦU PHÂN TÍCH (Khoảng 200 - 300 Từ):
Viết 1 đoạn văn phân tích thật chi tiết, sâu sắc mang góc nhìn của Giám Đốc Phân Tích Định Lượng (Quant Director).
1. VNINDEX hiện tại đang Tích lũy, FOMO hay Phân phối? Rủi ro hiện diện ở đâu?
2. Phân tích chi tiết Dòng tiền (Khối lượng) đang CHẢY MẠNH NHẤT MUA RÒNG vào Ngành nào (Dựa vào số dương của sector_flow) và RÚT ĐÁY KHỎI Ngành nào?
3. Nêu bật sự dịch chuyển (Rotation) giữa các cụm ngành và đánh giá đây là nhịp chốt lời cơ cấu hay là tháo chạy diện rộng.
Tuyệt đối KHÔNG VIẾT JSON. Chỉ sử dụng ngôn từ chuyên gia sắc bén, cung cấp góc nhìn đa chiều.
        """
        try:
            return self.model.generate_content(prompt).text.strip()
        except Exception as e:
            return f"Lỗi AI: Nguồn cấp nghẽn ({e})."

gemini_service = GeminiService()
