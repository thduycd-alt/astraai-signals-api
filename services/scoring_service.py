from services.gemini_service import gemini_service

class ScoringService:
    """
    Layer 7: Tổng hợp & Khuyến nghị Tiếng Việt (Trọng số)
    Kỹ thuật (25%) + Dòng tiền (25%) + Cơ bản (15%) + Vĩ mô (10%) + Tin đồn (15%) + Intraday (10%)
    """

    # Trọng số cố định chuẩn MVP
    WEIGHTS = {
        "technical": 0.25,
        "smart_money": 0.25,
        "fundamental": 0.15,
        "macro": 0.10,
        "news_rumor": 0.15,
        "intraday": 0.10
    }

    @staticmethod
    def calculate_final(symbol: str, layers_data: dict) -> dict:
        try:
            total_score = 0.0
            
            # Tính điểm trung bình có trọng số cho 6 tầng
            for layer_name, weight in ScoringService.WEIGHTS.items():
                layer_result = layers_data.get(layer_name, {})
                layer_score = layer_result.get("score", 50) # Mặc định 50 (Neutral) nếu lỗi data
                total_score += (layer_score * weight)
            
            final_score = round(total_score, 1)

            # Inject in-place the Expert Texts into layers_data for Frontend V2
            ScoringService._inject_expert_analysis(layers_data)
            
            # Khung Logic Mặc Định (Nếu Rớt mạng hoặc Không cắm Key)
            recommendation = "Giữ"
            action = "HOLD"
            
            if final_score >= 85:
                recommendation = "Mua mạnh (Cơ hội lớn, Dòng tiền & Vĩ mô cực kỳ ủng hộ)"
                action = "STRONG_BUY"
            elif 70 <= final_score < 85:
                recommendation = "Mua thận trọng (Theo dõi dòng tiền Mồi, có thể giải ngân nền)"
                action = "BUY"
            elif 50 <= final_score < 70:
                recommendation = "Giữ (Chưa rõ xu hướng đột phá lớn)"
                action = "HOLD"
            elif 30 <= final_score < 50:
                recommendation = "Bán thận trọng (Hạ tỷ trọng margin để an toàn)"
                action = "SELL"
            else:
                recommendation = "Bán / Tránh xa (Rủi ro Sập Gãy, Lực bán tháo cực lớn)"
                action = "STRONG_SELL"

            final_payload = {
                "final_score": final_score,
                "recommendation": recommendation,
                "action": action,
                "disclaimer": "Lưu ý: AstraAI Signals Khuyến nghị Tự Nắm Nguồn Lực. Miễn trừ mọi rủi ro đầu tư."
            }

            # ==============================================================
            # BƯỚC 3: GỌI SIÊU CHUYÊN GIA GEMINI 2.5 FLASH (V3 ENTERPRISE)
            # ==============================================================
            if gemini_service.model is not None:
                # V3: Gửi Toàn bộ Bể Dữ liệu Thô (Khối ngoại, Lệnh, PE, Vĩ mô) cho Gemini tự luận giải
                gemini_result = gemini_service.synthesize_analysis(symbol, layers_data)
                
                # Trộn Nhận Định Tổng Quan Chốt Hạ
                final_payload["recommendation"] = gemini_result.get("recommendation", recommendation)
                # KIỂM SOÁT QUYỀN LỰC AI: Đóng băng Điểm Toán Học, Không cho AI (Gemini) ghi đè để bảo vệ tính công bằng
                # final_payload["final_score"] = float(gemini_result.get("final_score", final_score))
                final_payload["action"] = gemini_result.get("action", action)
                final_payload["disclaimer"] = gemini_result.get("disclaimer", final_payload["disclaimer"])
                final_payload["v4_metrics"] = gemini_result.get("v4_metrics", {
                    "compression_score": 50,
                    "whale_style": "Đang phân tích dòng tiền...",
                    "hunting_zones": []
                })

                # Cập nhật Text 6 Tầng — CHỈ override nếu Gemini trả về nội dung có nghĩa
                def _safe_set(layer_key, gemini_key):
                    txt = gemini_result.get(gemini_key, "")
                    if txt and str(txt).strip():  # chỉ ghi đè nếu không rỗng
                        layers_data.get(layer_key, {})["expert_text"] = str(txt).strip()
                _safe_set("technical",   "tech_text")
                _safe_set("smart_money", "sm_text")
                _safe_set("fundamental", "fundamental_text")
                _safe_set("macro",       "macro_text")
                _safe_set("news_rumor",  "news_text")
                _safe_set("intraday",    "intraday_text")

            return final_payload
            
        except Exception as e:
            print(f"Scoring Analysis Error: {e}")
            return {"final_score": 50, "recommendation": "Lỗi tổng hợp dữ liệu", "action": "ERROR"}

    @staticmethod
    def _inject_expert_analysis(layers: dict):
        tech, ts = layers.get("technical", {}), layers.get("technical", {}).get("score", 50)
        rsi_val = layers.get("technical", {}).get("indicators", {}).get("rsi_14", 50)
        macd_status = layers.get("technical", {}).get("indicators", {}).get("macd_status", "")
        divergence = layers.get("technical", {}).get("divergence_signal", "")
        stoch_k = layers.get("technical", {}).get("indicators", {}).get("stoch_rsi_k", 50)
        trend_txt = layers.get("technical", {}).get("trend", "")
        action_txt = layers.get("technical", {}).get("price_action_setup", "")
        smc_txt = layers.get("technical", {}).get("smc_signal", "")

        divergence_line = f" Phân kỳ: {divergence}." if divergence and "Không có" not in divergence else ""
        stoch_line = f" Stoch RSI: {stoch_k:.0f}/100 ({'quá mua — thận trọng' if stoch_k > 75 else 'quá bán — cơ hội' if stoch_k < 25 else 'trung tính'})." if stoch_k != 50 else ""

        tech["layer_title"] = "Tầng 1: Kỹ Thuật (25%)"
        tech["color_hex"] = "#448AFF"
        tech["expert_text"] = (f"Xu hướng cốt lõi: {trend_txt}. RSI(14) = {rsi_val:.1f} — "
            f"{'vùng quá bán hấp dẫn' if rsi_val < 35 else 'quá mua cần thận' if rsi_val > 65 else 'trung tính'}. "
            f"MACD: {macd_status}. Mô hình giá: {action_txt}. SMC: {smc_txt}.{divergence_line}{stoch_line} "
            f"Hệ thống chấm {'mạnh' if ts >= 70 else 'yếu' if ts < 40 else 'trung bình'} {ts}/100 Tầng Kỹ Thuật.")

        sm, sms = layers.get("smart_money", {}), layers.get("smart_money", {}).get("score", 50)
        net_shark = sm.get("volume_analysis", {}).get("net_shark_vol", 0)
        cmf_val   = sm.get("cmf", {}).get("value", 0)
        obv_trend = sm.get("obv_trend", "")
        vol_mult  = sm.get("volume_analysis", {}).get("vol_multiplier", 1.0)
        shark_action = "GOM RÒNG" if net_shark > 0 else "XẢ RÒNG"
        shark_qty = abs(net_shark / 1_000_000)

        sm["layer_title"] = "Tầng 2: Smart Money (25%)"
        sm["color_hex"] = "#18FFFF"
        sm["expert_text"] = (f"Dòng tiền thông minh chấm điểm {sms}/100. "
            f"OBV: {obv_trend}. CMF(20) = {cmf_val:+.3f} — {'lực cầu mạnh' if cmf_val > 0.05 else 'lực cung áp đảo' if cmf_val < -0.05 else 'cân bằng'}. "
            f"15 phiên gần nhất: Cá mập đã {shark_action} {shark_qty:.1f}M cổ phiếu. "
            f"Khối lượng phiên này {'bùng nổ x3+ lần TB20 — dấu hiệu tay to tham gia tức thì.' if vol_mult >= 3 else f'= {vol_mult:.1f}x TB20.'} " 
            f"{'Tiềm năng gom hàng tốt.' if sms >= 60 else 'Cầnh giác xả lưu ý.' if sms < 40 else 'Giàng co chưa rõ.'}")  

        fd, fds = layers.get("fundamental", {}), layers.get("fundamental", {}).get("score", 50)
        fd["layer_title"] = "Tầng 3: Cơ Bản (15%)"
        fd["color_hex"] = "#B2FF59"
        fd["expert_text"] = f"Xét về nền tảng doanh nghiệp, điểm cơ bản đạt {fds}/100. Cấu trúc tài chính và định giá P/E, P/B hiện tại đang {'nằm trong vùng chiết khấu cực kỳ hấp dẫn so với giá trị thực.' if fds >= 65 else 'ở mức định giá phù hợp trung bình ngành, rủi ro cơ bản được kiểm soát.' if fds >= 45 else 'bộc lộ một số rủi ro đòn bẩy hoặc định giá đã quá cao so với lợi nhuận lõi.'} Tiềm năng biên lợi nhuận cốt lõi trong thời gian tới được dự phóng {'rất khả quan.' if fds >= 50 else 'đang gặp lực cản vĩ mô.'}"

        mc, mcs = layers.get("macro", {}), layers.get("macro", {}).get("score", 50)
        macro_news = layers.get("macro", {}).get("metrics", {}).get("latest_macro_news", [])
        m_txt = f" Tin nóng Vĩ mô: {macro_news[0]} | {macro_news[1]}" if len(macro_news) >= 2 else ""
        mc["layer_title"] = "Tầng 4: Vĩ Mô (10%)"
        mc["color_hex"] = "#FF8A65"
        mc["expert_text"] = f"Bối cảnh vĩ mô và chỉ số sức mạnh thị trường chung (VN-Index) đang tác động {'rất thuận lợi' if mcs >= 60 else 'tương đối đi ngang' if mcs >= 45 else 'cực kỳ tiêu cực'} đến nhóm ngành này. Điểm vĩ mô đạt {mcs}/100. Thời điểm hiện tại rổ tin tức ghi nhận:{m_txt}. Tác động liên đới ủng hộ kịch bản {'giải ngân.' if mcs >= 50 else 'phòng thủ tối đa.'}"

        nw, nws = layers.get("news_rumor", {}), layers.get("news_rumor", {}).get("score", 50)
        stock_news = nw.get("latest_headlines", [])
        s_txt = f" Điểm tin CafeF: {stock_news[0]} | {stock_news[1]}" if len(stock_news) >= 2 else ""
        nw["layer_title"] = "Tầng 5: Rumors & News (15%)"
        nw["color_hex"] = "#E040FB"
        nw["expert_text"] = f"Hệ thống tracking bề mặt báo chí tài chính chấm điểm {nws}/100. Cảm xúc trên các mặt báo đang rất {'FOMO và Hưng phấn.' if nws >= 80 else 'tích cực.' if nws >= 60 else 'ảm đạm và dè dặt.' if nws >= 40 else 'hoảng loạn và ngập lụt tin FUD.'}{s_txt}. Tác động tâm lý này có thể ảnh hưởng rất mạnh đến biến động T+ của nhỏ lẻ."

        ind, inds = layers.get("intraday", {}), layers.get("intraday", {}).get("score", 50)
        ind["layer_title"] = "Tầng 6: Dòng Thời Gian Tức Thời (10%)"
        ind["color_hex"] = "#FFD740"
        ind["expert_text"] = f"Phân tích Intraday tần số cao tại nến 3m/5m chấm điểm {inds}/100. Các thuật toán vi mô phát hiện {'có dòng lệnh tay to mồi kéo giá lên nhanh chóng' if inds >= 65 else 'nhịp đi ngang sideway biên độ hẹp' if inds >= 40 else 'áp lực bán tháo chủ động chớp nhoáng tại vùng giá cao'} trong phiên giao dịch hôm nay. Sóng luân chuyển tiền đang {'ủng hộ kịch bản mua lướt sóng T0.' if inds >= 60 else 'cảnh báo nhà đầu tư tuyệt đối không FOMO mua xanh.'}"

scoring_service = ScoringService()
