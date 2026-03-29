import json, os, time
from services.gemini_service import gemini_service
from services.fundamental_service import FundamentalService

_CACHE_DIR = "/tmp"  # Persist within Render instance

class RAGValuationService:
    """
    V6.3 — Hệ thống Định Giá Tầm Soát AI (Forward EPS & P/E RAG Engine)
    Dùng file-based cache (/tmp) thay vì in-memory để tránh mất kết quả khi Render khởi động lại.
    Cache 6h theo symbol.
    """

    @staticmethod
    def _cache_path(symbol: str) -> str:
        return os.path.join(_CACHE_DIR, f"rag_cache_{symbol}.json")

    @staticmethod
    def _load_cache(symbol: str) -> dict:
        try:
            path = RAGValuationService._cache_path(symbol)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                if time.time() - data.get('time', 0) < 21600:  # 6h
                    return data
        except:
            pass
        return {}

    @staticmethod
    def _save_cache(symbol: str, data: dict):
        try:
            path = RAGValuationService._cache_path(symbol)
            with open(path, 'w') as f:
                json.dump(data, f)
        except:
            pass


    @staticmethod
    async def project_valuation(symbol: str, current_price: float, recent_news: str,
                                trailing_eps: float = 0.0, yoy_growth: float = 0.0,
                                industry_pe: float = 0.0) -> dict:
        now = time.time()

        # Lấy fallback từ FundamentalService nếu chưa có
        if industry_pe <= 0:
            industry_pe = FundamentalService._get_industry_pe(symbol)
        if trailing_eps <= 0:
            trailing_eps = FundamentalService._get_default_eps(symbol, current_price)

        cached = RAGValuationService._load_cache(symbol)
        if cached:
            eps       = cached['eps']
            pe        = cached['pe']
            reasoning = cached['reasoning']
        else:
            # Prompt đầy đủ — Gemini có đủ số liệu để tầm soát thực sự
            prompt = f"""
Bạn là Chuyên gia Phân tích Cơ bản theo phương pháp "Tầm Soát Cổ Phiếu" của Trường Money.

=== DỮ LIỆU ĐẦU VÀO (ĐÃ ĐƯỢC HỆ THỐNG TRÍCH XUẤT) ===
- Mã cổ phiếu: {symbol}
- Giá thị trường hiện tại: {current_price:,.0f} VNĐ
- EPS Trailing 12 tháng (TTM) thực tế: {trailing_eps:,.0f} VNĐ/CP
- Tốc độ tăng trưởng LNST YoY gần nhất: {yoy_growth:.1f}%
- P/E ngành bình quân thị trường VN: {industry_pe:.1f}x
- Tin tức kinh doanh mới nhất: {recent_news[:800]}

=== NHIỆM VỤ TẦM SOÁT (5 BƯỚC) ===
Bước 1: Đánh giá chất lượng EPS Trailing ({trailing_eps:,.0f}) — có bền vững không, có yếu tố một lần không?
Bước 2: Dự phóng tăng trưởng LNST 4 quý tới dựa trên: chu kỳ ngành, vĩ mô, kế hoạch ĐHCĐ (rút từ tin tức).
Bước 3: Tính Forward EPS = EPS Trailing × (1 + Growth%). Kết quả cụ thể tới đồng.
Bước 4: Lựa chọn P/E mục tiêu: Cơ sở từ P/E ngành ({industry_pe:.1f}x), điều chỉnh theo tốc độ tăng trưởng và rủi ro.
         Quy tắc: Tăng trưởng >20% → P/E có thể cao hơn ngành. Rủi ro cao → giảm P/E biên an toàn.
Bước 5: Fair Value = Forward EPS × P/E Mục Tiêu.

=== YÊU CẦU ĐẦU RA (JSON THUẦN — KHÔNG CHÚ THÍCH BÊN NGOÀI) ===
{{
    "trailing_eps_assessment": "<1-2 câu đánh giá EPS trailing có sạch không, có bất thường không>",
    "growth_projection": "<% tăng trưởng LNST kỳ vọng 12 tháng tới, giải thích bằng số cụ thể>",
    "forward_eps": <số float — Forward EPS tính được>,
    "target_pe": <số float — P/E mục tiêu đã luận chứng>,
    "pe_reasoning": "<Tại sao chọn P/E này? So sánh với lịch sử ngành và tốc độ tăng trưởng>",
    "reasoning": "<Đoạn văn 4-5 câu tổng hợp: EPS → Growth → Forward EPS → P/E → Fair Value và luận điểm tầm soát>"
}}
"""
            eps     = trailing_eps
            pe      = industry_pe
            reasoning = "Dùng EPS trailing và P/E ngành (AI chưa phản hồi)."
            ai_extras = {}

            try:
                ai_response = gemini_service.model.generate_content(
                    prompt,
                    generation_config=__import__('google.generativeai', fromlist=['generativeai']).GenerationConfig(
                        response_mime_type="application/json"
                    )
                ).text
                data = json.loads(ai_response)

                forward_eps = float(data.get("forward_eps", trailing_eps))
                target_pe   = float(data.get("target_pe",   industry_pe))

                # Ràng buộc hallucination
                if forward_eps <= 0:     forward_eps = trailing_eps
                if target_pe   <= 0 or target_pe > 50: target_pe = industry_pe

                eps       = forward_eps
                pe        = target_pe
                reasoning = data.get("reasoning", "")
                ai_extras = {
                    "trailing_eps_assessment": data.get("trailing_eps_assessment", ""),
                    "growth_projection":       data.get("growth_projection", ""),
                    "pe_reasoning":            data.get("pe_reasoning", ""),
                }

                RAGValuationService._save_cache(symbol, {
                    'time': now, 'eps': eps, 'pe': pe,
                    'reasoning': reasoning, 'extras': ai_extras
                })
            except Exception as e:
                print(f"[{symbol}] RAG Valuation AI error: {e}")
                reasoning = f"AI tạm thời không khả dụng. Dùng EPS trailing {trailing_eps:,.0f} × P/E ngành {industry_pe:.1f}x."
                ai_extras = {}

        # Tính giá trị — LUÔN DYNAMIC theo current_price thực
        fair_value = FundamentalService._round_to_tick(eps * pe)
        upside     = ((fair_value - current_price) / current_price) * 100 if current_price > 0 else 0
        mos_zones  = FundamentalService._build_mos_zones(fair_value, current_price)

        # Lấy extras từ cache nếu có
        cached_now = RAGValuationService._load_cache(symbol)
        extras     = cached_now.get('extras', {})

        return {
            "score": 65 if eps > trailing_eps else 50,
            "metrics": {
                "PE":              round(pe, 2),
                "PB":              1.5,
                "EPS":             round(eps, 2),
                "ROE_Percent":     15.0,
                "Fair_Value":      fair_value,
                "Upside":          round(upside, 2),
                "Reference_Price": fair_value,
                "AI_Reasoning":    reasoning,
                "mos_zones":       mos_zones,
                "pe_evaluation":   FundamentalService._pe_label(pe, industry_pe),
                "industry_pe":     industry_pe,
                "trailing_eps":    round(trailing_eps, 2),
                "yoy_growth_pct":  round(yoy_growth, 2),
                "ai_trailing_assessment": extras.get("trailing_eps_assessment", ""),
                "ai_growth_projection":   extras.get("growth_projection", ""),
                "ai_pe_reasoning":        extras.get("pe_reasoning", ""),
            },
            "status": "Phân Tích AI RAG Tầm Soát 🟢"
        }

rag_valuation_service = RAGValuationService()
