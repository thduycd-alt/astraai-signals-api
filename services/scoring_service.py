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
    def calculate_final(layers_data: dict) -> dict:
        try:
            total_score = 0.0
            
            # Tính điểm trung bình có trọng số cho 6 tầng
            for layer_name, weight in ScoringService.WEIGHTS.items():
                layer_result = layers_data.get(layer_name, {})
                layer_score = layer_result.get("score", 50) # Mặc định 50 (Neutral) nếu lỗi data
                total_score += (layer_score * weight)
            
            final_score = round(total_score, 1)
            
            # Khung Logic "Khuyến nghị" (Recommendation)
            recommendation = "Giữ"
            action = "HOLD"
            
            if final_score >= 85:
                recommendation = "Mua mạnh (Vùng Cơ hội lớn, Dòng tiền & Vĩ mô cực kỳ ủng hộ)"
                action = "STRONG_BUY"
            elif 70 <= final_score < 85:
                recommendation = "Mua thận trọng (Có thể giải ngân 30-50% lấy vị thế)"
                action = "BUY"
            elif 50 <= final_score < 70:
                recommendation = "Giữ (Chưa rõ xu hướng đột phá, theo dõi thêm)"
                action = "HOLD"
            elif 30 <= final_score < 50:
                recommendation = "Bán thận trọng (Hạ tỷ trọng margin, chốt lời một phần)"
                action = "SELL"
            else:
                recommendation = "Bán / Tránh (Rủi ro cực cao, dòng tiền lớn thoát ra)"
                action = "STRONG_SELL"

            return {
                "final_score": final_score,
                "recommendation": recommendation,
                "action": action,
                "disclaimer": "Lưu ý: AstraAI Signals chỉ hỗ trợ ra quyết định. Miễn trừ mọi rách nhiệm về rủi ro đầu tư."
            }
            
        except Exception as e:
            print(f"Scoring Analysis Error: {e}")
            return {"final_score": 50, "recommendation": "Lỗi tổng hợp dữ liệu", "action": "ERROR"}

scoring_service = ScoringService()
