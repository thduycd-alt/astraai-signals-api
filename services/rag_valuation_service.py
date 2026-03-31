import json, os, time
from services.gemini_service import gemini_service
from services.fundamental_service import FundamentalService

def _call_vs_bctc(symbol: str) -> str:
    try:
        from services.vietstock_bctc_service import get_bctc_for_ai
        return get_bctc_for_ai(symbol)
    except Exception as e:
        print(f'[WARN] vietstock_bctc_service: {e}')
        return ''


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
                                industry_pe: float = 0.0, actual_pe: float = 0.0,
                                hist_avg_pe: float = 0.0,
                                pb_actual: float = 0.0, book_value_per_share: float = 0.0) -> dict:
        now = time.time()

        # Lấy fallback từ FundamentalService nếu chưa có
        if industry_pe <= 0:
            industry_pe = FundamentalService._get_industry_pe(symbol)
        if trailing_eps <= 0:
            trailing_eps = FundamentalService._get_default_eps(symbol, current_price)

        # === PE CEILING: neo PE mục tiêu vào giá trị thực tế ===
        # Giới hạn tối đa = min(PE ngành, PE thực x 1.5)
        # Tránh AI chọn PE = 24x khi thị trường đang định giá cổ phiếu tại PE = 9.63x
        if actual_pe > 0.5:
            raw_ceiling = min(industry_pe, actual_pe * 1.5)
            pe_ceiling  = max(raw_ceiling, actual_pe)  # ít nhất bằng PE hiện tại
        elif hist_avg_pe > 0.5:
            pe_ceiling  = min(industry_pe, hist_avg_pe * 1.2)
        else:
            pe_ceiling  = industry_pe  # fallback khi không có dữ liệu
        pe_ceiling = round(pe_ceiling, 1)
        print(f"[{symbol}] RAG PE ceiling={pe_ceiling} (actual={actual_pe}, industry={industry_pe}, hist5yr={hist_avg_pe})")

        # BVPS: luôn tính từ giá/P/B để đảm bảo nhất quán (không tin giá trị từ fundamental_service)
        if pb_actual > 0:
            book_value_per_share = current_price / pb_actual
        # Industry blend weights: backend quyết định, không tin Gemini JSON
        # BĐS (industry_pe 15-28) + Ngân hàng (pe < 12): PB quan trọng hơn
        if industry_pe <= 12 or (14 <= industry_pe <= 30):
            _default_pe_w, _default_pb_w = 0.30, 0.70   # BĐS & Ngân hàng
        else:
            _default_pe_w, _default_pb_w = 0.70, 0.30   # Tech / Bán lẻ / Chứng khoán
        print(f"[{symbol}] Industry blend: PE={_default_pe_w:.0%} PB={_default_pb_w:.0%}, BVPS={book_value_per_share:,.0f}")

        cached = RAGValuationService._load_cache(symbol)
        # Invalidate cache nếu yoy_growth thay đổi đáng kể (>2%)
        cached_yoy = cached.get('yoy', None) if cached else None
        if cached and cached_yoy is not None and abs(cached_yoy - yoy_growth) > 2.0:
            print(f"[{symbol}] Cache invalidated: yoy changed {cached_yoy:.1f}% -> {yoy_growth:.1f}%")
            cached = None

        # === Khởi tạo params với fallback ===
        forward_eps = trailing_eps
        target_pe   = pe_ceiling
        target_pb   = pb_actual if pb_actual > 0 else 1.2
        reasoning   = "Dung EPS trailing va P/E nganh (AI chua phan hoi)."
        ai_extras   = {}

        if cached:
            # Chi load PARAMS, khong load FV (FV se tinh lai ben duoi)
            forward_eps = cached.get('eps',        trailing_eps)
            target_pe   = cached.get('pe',         industry_pe)
            target_pb   = cached.get('target_pb',  pb_actual if pb_actual > 0 else 1.2)
            reasoning   = cached.get('reasoning',  reasoning)
            ai_extras   = cached.get('extras',     {})
        else:
            # Fetch Vietstock BCTC balance sheet data
            _bctc_txt = _call_vs_bctc(symbol)
            bctc_section = f'\n=== DU LIEU BCTC BALANCE SHEET (NGUON: VIETSTOCK FINANCE) ===\n{_bctc_txt}' if _bctc_txt else ''

            # Prompt đầy đủ — Gemini có đủ số liệu để tầm soát thực sự
            prompt = f"""
Bạn là Chuyên gia Phân tích Cơ bản theo phương pháp "Tầm Soát Cổ Phiếu" của Trường Money.

=== DỮ LIỆU ĐẦU VÀO (ĐÃ ĐƯỢC HỆ THỐNG TRÍCH XUẤT) ===
- Mã cổ phiếu: {symbol}
- Giá thị trường hiện tại: {current_price:,.0f} VNĐ
- EPS Trailing 12 tháng (TTM) thực tế: {trailing_eps:,.0f} VNĐ/CP
- Giá trị sổ sách trên mỗi cổ phiếu (BVPS): {book_value_per_share:,.0f} VNĐ/CP
- P/E thực tế hiện nay: {actual_pe:.1f}x. P/B thực tế: {pb_actual:.1f}x.
- Tốc độ tăng trưởng LNST YoY gần nhất: {yoy_growth:.1f}%
- P/E ngành bình quân thị trường VN: {industry_pe:.1f}x. Lịch sử PE 5 năm: {hist_avg_pe:.1f}x.
- Tin tức kinh doanh mới nhất: {recent_news[:800]}
{bctc_section}

=== NHIỆM VỤ TẦM SOÁT (5 BƯỚC) ===
Bước 1: Đánh giá chất lượng EPS Trailing ({trailing_eps:,.0f}) — có bền vững không, có yếu tố một lần không?
Bước 2: Dự phóng tăng trưởng LNST 4 quý tới. PHẢI sử dụng dữ liệu BCTC Balance Sheet bên trên (nếu có) để phân tích:
         - Hàng tồn kho tăng/giảm → tiềm năng bàn giao doanh thu?
         - Người mua trả trước (advance from customers) tăng mạnh → đã thu tiền, sắp ghi nhận doanh thu?
         - Dòng tiền OCF → cash generation thực sự
         - Kết hợp với chu kỳ ngành, vĩ mô, tin tức.
Bước 3: Tính Forward EPS = EPS Trailing × (1 + Growth%). Kết quả cụ thể tới đồng.
Bước 4: Xác định Bội số Định giá (PE và PB) theo NGÀNH THỰC TẾ VN:
         PE target: Ngân hàng 7-10x, BĐS phục hồi/pipeline lớn 15-22x, BĐS khó khăn/lỗ 8-12x, Thép chu kỳ 6-9x, Chứng khoán 10-14x, Bán lẻ/Tech 12-20x
         PB target: Ngân hàng 1.2-2.0x, BĐS 1.0-2.0x, Thép 0.8-1.2x, Chứng khoán 1.5-3.0x
         Tỷ trọng blend theo ngành:
         - BĐS & Ngân hàng: blend 30% PE + 70% PB (PB ổn định hơn khi EPS biến động)
         - Thép & Hóa chất chu kỳ: blend 50% PE + 50% PB
         - Bán lẻ & Tech & Chứng khoán: blend 80% PE + 20% PB
Bước 5: Tính Fair Value bằng công thức blend PE/PB:
         - FV_PE_base = Forward EPS × PE_target_mid
         - FV_PB_base = BVPS ({book_value_per_share:,.0f} VNĐ) × PB_target_mid
         - FV_Mid = (trọng số PE × FV_PE_base) + (trọng số PB × FV_PB_base)
         - FV_Low = FV_Mid × 0.85 (kịch bản xấu — PE/PB ở mức thấp của dải)
         - FV_High = FV_Mid × 1.20 (kịch bản tốt — PE/PB ở mức cao của dải)
         Ghi rõ số tính được cho từng thành phần.

=== YÊU CẦU ĐẦU RA (JSON THUẦN — KHÔNG CHÚ THÍCH BÊN NGOÀI) ===
⚠️ KHÔNG tự tính fair_value_low/mid/high — backend sẽ tính từ tham số bạn cung cấp.
{{
    "trailing_eps_assessment": "<1-2 câu đánh giá EPS trailing có sạch không>",
    "growth_projection": "<% tăng trưởng LNST kỳ vọng 12 tháng tới, có đề cập BCTC nếu có>",
    "forward_eps": <số float — EPS Trailing × (1 + growth%)>,
    "target_pe":   <số float — P/E mục tiêu cho kịch bản base case>,
    "target_pb":   <số float — P/B mục tiêu cho kịch bản base case>,
    "pe_weight":   <số float 0.0-1.0 — tỷ trọng PE trong blend, ví dụ 0.3 cho BĐS>,
    "pb_weight":   <số float 0.0-1.0 — tỷ trọng PB trong blend, ví dụ 0.7 cho BĐS>,
    "pe_reasoning": "<Giải thích: tại sao chọn PE/PB này? FV_PE_base = Forward EPS × target_pe = X; FV_PB_base = BVPS × target_pb = Y; FV_Mid = pe_weight×X + pb_weight×Y = Z>",
    "reasoning": "<4-5 câu tổng hợp: EPS trailing → tăng trưởng → PE/PB blend → FV 3 kịch bản>"
}}
"""
            # === Khởi tạo params từ fallback ===
            forward_eps = trailing_eps
            target_pe   = pe_ceiling
            target_pb   = pb_actual if pb_actual > 0 else 1.2
            reasoning   = "Dùng EPS trailing và P/E ngành (AI chưa phản hồi)."
            ai_extras   = {}

            try:
                ai_response = gemini_service.model.generate_content(
                    prompt,
                    generation_config=__import__('google.generativeai', fromlist=['generativeai']).GenerationConfig(
                        response_mime_type="application/json"
                    )
                ).text
                data = json.loads(ai_response)

                _feps = float(data.get("forward_eps", trailing_eps))
                _tpe  = float(data.get("target_pe",   industry_pe))
                _tpb  = float(data.get("target_pb",   pb_actual if pb_actual > 0 else 1.2))

                if _feps > 0: forward_eps = _feps
                if _tpe  > 0: target_pe   = _tpe
                if _tpb  > 0: target_pb   = _tpb

                reasoning = data.get("reasoning", reasoning)
                ai_extras = {
                    "trailing_eps_assessment": data.get("trailing_eps_assessment", ""),
                    "growth_projection":       data.get("growth_projection", ""),
                    "pe_reasoning":            data.get("pe_reasoning", ""),
                }
            except Exception as e:
                print(f"[{symbol}] RAG Valuation AI error: {e}")

            # === Tính FV — done OUTSIDE if/else ===
            # (save cache voi params, khong save FV)
            RAGValuationService._save_cache(symbol, {
                'time': now, 'eps': forward_eps, 'pe': target_pe,
                'target_pb': target_pb,
                'yoy': yoy_growth,
                'reasoning': reasoning, 'extras': ai_extras,
            })

        # === FV LUON TINH TAI DAY (sau ca if/else) voi BVPS hien tai ===
        eps = forward_eps
        pe  = target_pe
        fv_pe_base = eps * pe
        fv_pb_base = book_value_per_share * target_pb
        fv_mid_raw = _default_pe_w * fv_pe_base + _default_pb_w * fv_pb_base
        fair_value_mid  = FundamentalService._round_to_tick(fv_mid_raw)
        fair_value_low  = FundamentalService._round_to_tick(fair_value_mid * 0.85)
        fair_value_high = FundamentalService._round_to_tick(fair_value_mid * 1.20)
        print(f"[{symbol}] FV FINAL: EPS={eps:.0f}xPE{pe:.1f}={fv_pe_base:.0f} | BVPS={book_value_per_share:.0f}xPB{target_pb:.1f}={fv_pb_base:.0f} | Blend({_default_pe_w:.0%}+{_default_pb_w:.0%})=FV{fair_value_mid:.0f}")

        # Append FV summary to reasoning
        reasoning += (
            f"\n\n=== Ket qua dinh gia blend {_default_pe_w:.0%} PE + {_default_pb_w:.0%} PB ==="
            f"\n- FV_PE = {eps:,.0f} x {pe:.1f}x = {fv_pe_base:,.0f} VND"
            f"\n- FV_PB = BVPS {book_value_per_share:,.0f} x {target_pb:.1f}x = {fv_pb_base:,.0f} VND"
            f"\n- Kem: {fair_value_low:,.0f} | Co so: {fair_value_mid:,.0f} | Tot: {fair_value_high:,.0f} VND/CP"
        )

        # Tick-round FV_mid để Zone 1 (scenario boxes) = Zone 2 (MoS bar)
        fair_value_mid = FundamentalService._round_to_tick(fair_value_mid)
        fair_value_low = FundamentalService._round_to_tick(fair_value_low)
        fair_value_high = FundamentalService._round_to_tick(fair_value_high)

        upside     = ((fair_value_mid - current_price) / current_price) * 100 if current_price > 0 else 0
        mos_zones  = FundamentalService._build_mos_zones(fair_value_mid, current_price)

        # Lấy extras từ cache nếu có
        cached_now = RAGValuationService._load_cache(symbol)
        extras     = cached_now.get('extras', {})

        return {
            "score": 65 if eps > trailing_eps else 50,
            "metrics": {
                "PE":              round(pe, 2),
                "PB":              round(pb_actual, 2) if pb_actual > 0 else 1.5,
                "EPS":             round(eps, 2),
                "ROE_Percent":     15.0,
                "Fair_Value":      fair_value_mid,
                "Fair_Value_Low":  fair_value_low,
                "Fair_Value_Mid":  fair_value_mid,
                "Fair_Value_High": fair_value_high,
                "Upside":          round(upside, 2),
                "Reference_Price": fair_value_mid,
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
