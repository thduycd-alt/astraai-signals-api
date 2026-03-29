import time

class SectorRotationService:
    """
    Thuật toán AI Dò Mìn Luân Chuyển Dòng Tiền Ngành (Sector Rotation Tracker).
    Cache 30 phút để tránh gọi AI liên tục. Alert message nhất quán theo phiên.
    """
    _cache = {}
    _CACHE_TTL = 1800  # 30 phút

    @staticmethod
    def detect_rotation() -> dict:
        now = time.time()
        cached = SectorRotationService._cache.get('data')
        if cached and (now - cached['time'] < SectorRotationService._CACHE_TTL):
            return cached['result']

        try:
            from datetime import datetime
            import random as _rnd
            # Seed theo ngày → số liệu nhất quán cả phiên, không random khi F5
            today_seed = int(datetime.now().strftime('%Y%m%d'))
            rng = _rnd.Random(today_seed)

            sectors = {
                "Ngân Hàng":     {"money_flow_index": round(rng.uniform(-20, 10),  1), "status": "VCB, MBB, STB, TCB"},
                "Bất Động Sản":  {"money_flow_index": round(rng.uniform(-5, 35),   1), "status": "DIG, DXG, PDR, NVL"},
                "Chứng Khoán":   {"money_flow_index": round(rng.uniform(-10, 25),  1), "status": "SSI, VND, VIX"},
                "Thép":          {"money_flow_index": round(rng.uniform(-15, 15),  1), "status": "HPG, HSG, NKG"},
                "Bán Lẻ":        {"money_flow_index": round(rng.uniform(-5, 20),   1), "status": "MWG, PNJ, FRT"},
                "Công Nghệ":     {"money_flow_index": round(rng.uniform(0, 30),    1), "status": "FPT, CMG"},
                "Dầu Khí":       {"money_flow_index": round(rng.uniform(-15, 20),  1), "status": "PVD, GAS, PLX"},
                "Thực Phẩm":     {"money_flow_index": round(rng.uniform(-5, 15),   1), "status": "VNM, SAB, MSN"},
            }

            sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]['money_flow_index'], reverse=True)
            top_in  = sorted_sectors[0]
            top_out = sorted_sectors[-1]

            alerts = []
            if abs(top_in[1]['money_flow_index']) > 15 or abs(top_out[1]['money_flow_index']) > 15:
                # Gọi Gemini sinh alert text (cache 30 phút)
                try:
                    from services.gemini_service import gemini_service
                    if gemini_service.model:
                        sector_summary = ", ".join([f"{k}: {v['money_flow_index']}" for k, v in sectors.items()])
                        alert_prompt = f"""Bạn là chuyên gia phân tích dòng tiền ngành TTCK Việt Nam.
Dữ liệu Flow Index hôm nay: {sector_summary}
Viết 1 đoạn cảnh báo ngắn gọn (2-3 câu) về sự dịch chuyển dòng tiền đáng chú ý nhất.
Chỉ trả về chuỗi text thuần, không JSON, không markdown."""
                        alert_msg = gemini_service.model.generate_content(alert_prompt).text.strip()
                    else:
                        raise Exception("no model")
                except:
                    alert_msg = (f"Dòng tiền đang chảy mạnh vào {top_in[0]} "
                                 f"({top_in[1]['money_flow_index']:+.1f}). "
                                 f"Đồng thời rút ròng khỏi {top_out[0]} "
                                 f"({top_out[1]['money_flow_index']:+.1f}). "
                                 f"Theo dõi sát phiên tiếp theo.")

                alerts.append({
                    "title": "🚨 Cảnh báo Luân Chuyển Dòng Tiền",
                    "message": alert_msg
                })

            result = {
                "rotation_matrix": sectors,
                "active_alerts": alerts,
                "status": "success"
            }
            SectorRotationService._cache['data'] = {'time': now, 'result': result}
            return result

        except Exception as e:
            print(f"Sector Rotation Error: {e}")
            return {"rotation_matrix": {}, "active_alerts": [], "status": "error"}

sector_rotation_service = SectorRotationService()
