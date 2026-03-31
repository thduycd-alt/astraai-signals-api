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
    def calculate_final(symbol: str, layers_data: dict, c_price: float = 0.0) -> dict:
        try:
            total_score = 0.0
            
            # Tính điểm trung bình có trọng số cho 6 tầng
            for layer_name, weight in ScoringService.WEIGHTS.items():
                layer_result = layers_data.get(layer_name, {})
                layer_score = layer_result.get("score", 50) # Mặc định 50 (Neutral) nếu lỗi data
                total_score += (layer_score * weight)
            
            final_score = round(total_score, 1)


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
                # Gửi Toàn bộ Bể Dữ liệu Thô (Khối ngoại, Lệnh, PE, Vĩ mô) cho Gemini tự luận giải
                gemini_result = gemini_service.synthesize_analysis(symbol, layers_data)
                
                final_payload["recommendation"] = gemini_result.get("recommendation", recommendation)
                final_payload["action"] = gemini_result.get("action", action)
                final_payload["disclaimer"] = "Báo cáo Tự động tạo bởi Gemini AI theo chuẩn Tầm Soát 15 Tiêu Chí (Trường Money)."
                
                # Mảng chứa [hunting_zones] và v4 metrics
                final_payload["v4_metrics"] = gemini_result.get("v4_metrics", {
                    "compression_score": 50,
                    "whale_style": "Đang phân tích dòng tiền...",
                    "hunting_zones": []
                })

                # Gắn nguyên Bảng Chấm Điểm 15 Tiêu Chí vào Payload
                quality_data = {
                    "criteria_list": gemini_result.get("criteria_list", []),
                    "total_score": gemini_result.get("total_score", 0),
                    "max_score": gemini_result.get("max_score", 45),
                    "quality_rating": gemini_result.get("quality_rating", "N/A")
                }
                final_payload["quality_scoring"] = quality_data

                # OVERRIDE final_score bằng điểm 15 tiêu chí (quy đổi /100)
                # Đây là điểm CHÍNH hiển thị trên App, thay thế điểm 6 tầng cũ
                raw_quality_total = gemini_result.get("total_score", 0)
                max_quality = gemini_result.get("max_score", 45)
                if raw_quality_total > 0 and max_quality > 0:
                    final_payload["final_score"] = round((raw_quality_total / max_quality) * 100, 1)

                # Lấy sẵn kết quả định giá từ RAG (đã blend PE/PB chuẩn ở bước trước)
                base_metrics = layers_data.get("fundamental", {}).get("metrics", {})
                final_payload["smart_valuation"] = base_metrics

            # Xóa các Tầng Cũ (Chỉ giữ lại mảng trống hoặc xóa hẳn)
            layers_data.clear()

            return final_payload
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"Scoring Analysis Error: {error_msg}")
            return {"final_score": 50, "recommendation": f"Lỗi tổng hợp dữ liệu: {str(e)}\n\n{error_msg}", "action": "ERROR"}

scoring_service = ScoringService()
