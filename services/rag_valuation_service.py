import json
from services.gemini_service import gemini_service
from services.fundamental_service import FundamentalService

class RAGValuationService:
    """
    V6.1: Hệ thống Định Giá Tầm Soát AI (Forward EPS & P/E RAG Engine)
    Sử dụng Gemini 2.5 Flash để bóc tách, tự biên luận và dự phóng EPS Tương Lai
    thay vì dùng EPS Quá khứ (TTM) thô cứng. (Phương pháp Trường Money)
    """

    @staticmethod
    async def project_valuation(symbol: str, current_price: float, recent_news: str) -> dict:
        # Default Fallback (Ngành)
        default_pe = FundamentalService._get_industry_pe(symbol)
        default_eps = (current_price * 1.15) / default_pe if current_price > 0 else 1500.0

        prompt = f"""
ĐÓNG VAI: Chuyên gia Phân Tích Định Lượng (Quant) & Cơ bản thao tác theo "Phương pháp Tầm soát cổ phiếu" của Trường Money.
NHIỆM VỤ: Dự phóng Lợi Nhuận Tương Lai (Forward EPS) cho cổ phiếu {symbol} (Giá hiện tại: {current_price} VNĐ).
DỮ LIỆU ĐẦU VÀO: 
- Mã Cổ phiếu: {symbol}
- Tin tức cập nhật mới nhất: {recent_news} (Hãy trích xuất Keyword về mở rộng nhà máy, tăng trưởng...).

HƯỚNG DẪN TẦM SOÁT:
1. Dự đoán xu hướng kinh doanh (LNST) 4 quý tới của {symbol} dựa trên Vĩ mô và ngành nghề.
2. Ước lượng % tăng trưởng Lợi Nhuận (Growth margin).
3. Đưa ra con số Forward EPS hợp lý (Khoảng độ {default_eps * 0.8} tới {default_eps * 1.5}). Định ra con số Chính Xác.
4. Lựa chọn P/E Hợp lý (Khuyến nghị Ngành: {default_pe}). Sửa lại nếu vĩ mô tốt/xấu.

YÊU CẦU ĐẦU RA BẮT BUỘC (JSON ĐÚNG CHUẨN - KHÔNG VIẾT CHỮ BÊN NGOÀI):
{{
    "forward_eps": <Số float>,
    "target_pe": <Số float>,
    "reasoning": "<Đoạn văn 3-4 câu giải thích RÕ RÀNG luận điểm tại sao chọn cái EPS và P/E này (Dựa vào Kế Hoạch Kinh Doanh/Chu kỳ ngành)>"
}}
"""
        try:
            # Sinh ra kết quả RAG AI
            ai_response = gemini_service.model.generate_content(prompt).text.strip()
            
            # Xử lý dọn Code Block
            if ai_response.startswith("```json"): ai_response = ai_response[7:]
            if ai_response.endswith("```"): ai_response = ai_response[:-3]
            
            data = json.loads(ai_response.strip())
            
            eps = float(data.get("forward_eps", default_eps))
            pe = float(data.get("target_pe", default_pe))
            
            # Ràng buộc rủi ro Hallucination
            if eps <= 0: eps = default_eps
            if pe <= 0 or pe > 50: pe = default_pe
            
            fair_value = FundamentalService._round_to_tick(eps * pe)
            
            # Recalculate upside purely based on AI's Forward EPS and PE
            upside = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0
            
            return {
                "score": 60 if eps > default_eps else 40,
                "metrics": {
                    "PE": round(pe, 2),
                    "PB": 1.5, # fallbacks to maintain JSON shape
                    "EPS": round(eps, 2),
                    "ROE_Percent": 15.0,
                    "Fair_Value": fair_value,
                    "Upside": round(upside, 2),
                    "Reference_Price": FundamentalService._round_to_tick(current_price * 1.25) if current_price > 0 else fair_value,
                    "AI_Reasoning": data.get("reasoning", "Đang xử lý.")
                },
                "status": "Phân Tích AI RAG Tương Lai 🟢"
            }
            
        except Exception as e:
            print(f"[{symbol}] RAG Valuation Failed: {e}")
            fair_val_fb = FundamentalService._round_to_tick(default_eps * default_pe)
            return {
                "score": 50,
                "metrics": {
                    "PE": default_pe,
                    "PB": 1.5,
                    "EPS": round(default_eps, 2),
                    "ROE_Percent": 15.0,
                    "Fair_Value": fair_val_fb,
                    "Upside": 15.0,
                    "Reference_Price": FundamentalService._round_to_tick(current_price * 1.25),
                    "AI_Reasoning": "Lỗi kết nối Gemini RAG. Hệ thống dùng P/E Ngành bảo thủ."
                },
                "status": "Trung Lập (Dữ liệu Fallback) 🟡"
            }

rag_valuation_service = RAGValuationService()
