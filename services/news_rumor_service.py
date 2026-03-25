class NewsRumorService:
    """
    Layer 5: Tin tức, Rumor & Lập trường KOL (Trọng số 15%)
    Sử dụng Web Crawler (Cafef, F319) và Mạng lưới KOL.
    Đẩy qua NLP PhoBERT để tính Sentiment (-15 đến +15)
    """
    
    # Danh sách VIP KOL & Lãnh đạo cộm cán (Hệ thống tự học và Tracking phát ngôn/hành vi)
    # Admin/User có thể cấu hình và bổ sung thêm trực tiếp từ App Mobile.
    DEFAULT_KOLS = [
        "Trường Money", "A7", "Tuấn mượt", 
        "Phạm Nhật Vượng", "Bầu Thụy", "Bầu Đức"
    ]

    @staticmethod
    def analyze(symbol: str, custom_kols: list = None) -> dict:
        try:
            kols_to_track = custom_kols if custom_kols else NewsRumorService.DEFAULT_KOLS
            
            # 1. Blueprint Scraping Tin tức Đại chúng & F319
            # requests.get(f"https://cafef.vn/tim-kiem.chn?keyword={symbol}")
            
            # 2. Tracking Hành vi KOL (AI Learning Blueprint)
            # Hệ thống NLP sẽ quét các Post Text, Video Transcript liên quan đến KOLS_TO_TRACK
            
            # ĐĂC QUYỀN: Xử lý Lập trường KOL & Nhóm lợi ích
            mock_kol_stance = []
            kol_bonus_score = 0
            
            # Nhận diện hệ sinh thái: Tính năng liên kết Cổ Phiếu với Hành vi KOL (MVP Mock)
            if symbol in ["VIC", "VHM", "VRE"]:
                mock_kol_stance.append("Phạm Nhật Vượng: Chiến lược dồn lực cho VinFast và tái cấu trúc huy động vốn ngoại.")
                kol_bonus_score += 5
            elif symbol in ["DIG", "CEO", "L14"]:
                mock_kol_stance.append("Hệ A7 (Rumor): Đang có sóng kích cầu dư luận từ các Room VIP, kêu gào chu kỳ đất nền.")
                kol_bonus_score += 10
            elif symbol in ["LPB", "THD"]:
                mock_kol_stance.append("Bầu Thụy: Động thái thâu tóm và gom ròng đỡ giá cổ phiếu ngân hàng lộ rỏ qua lệnh block trades.")
                kol_bonus_score += 15  # Đỉnh cao cá mập
            elif symbol in ["GEX", "VIX", "EIB"]:
                mock_kol_stance.append("Tuấn Mượt: Có lịch sử đánh rát tay. Hiện tại đang xả hàng kéo xanh giả mạo, chú ý rủi ro phân phối đỉnh.")
                kol_bonus_score -= 15 # Trừ điểm kịch khung
            elif symbol in ["HAG", "HNG"]:
                mock_kol_stance.append("Bầu Đức: Phát ngôn dồn dập về trả nợ trái phiếu và bán mảng heo. Sự tự tin của Chủ tịch đang lên cao.")
                kol_bonus_score += 8
            
            # API Mock Output Tin tức chung
            mock_headlines = [
                f"Room VIP phím hàng {symbol} với target rất cao",
                f"{symbol} chuẩn bị công bố thông tin quan trọng"
            ]
            
            # 3. Chấm điểm Cảm xúc của PhoBERT (Scale: -15 to +15)
            phobert_raw_score = 8  # Tích cực nhẹ
            
            # TỔNG HỢP LAYER 5: Base (50) + Điểm Tin tức (PhoBERT x 1.5) + Điểm KOL
            score = 50 + (phobert_raw_score * 1.5) + kol_bonus_score

            return {
                "score": max(0, min(100, score)),
                "phobert_sentiment_raw": phobert_raw_score,
                "latest_headlines": mock_headlines,
                "kol_stances": mock_kol_stance,
                "tracked_kols_active": len(kols_to_track),
                "tracked_kols_list": kols_to_track,
                "status": "Bullish Rumors & KOL Hỗ trợ kéo giá" if score > 60 else 
                         ("Bearish (KOL đang xả hàng lên đầu nhỏ lẻ)" if score < 40 else "Neutral")
            }
            
        except Exception as e:
            print(f"News/Rumor/KOL Analysis Error: {e}")
            return {"error": str(e), "score": 50}

news_rumor_service = NewsRumorService()
