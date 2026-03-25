import pandas as pd

class MarketService:
    """
    Market Dashboard Service: Backend xử lý dữ liệu cho Dashboard Toàn Cảnh bằng API.
    Cung cấp data cho Biểu Đồ Nhiệt (Heatmap), Khối ngoại, Thanh khoản chung.
    """

    @staticmethod
    def get_overview() -> dict:
        try:
            # 1. Kéo API Index Realtime từ vnstock (VNINDEX, VN30, HNX)
            
            # Dữ liệu Mock Blueprint cho MVP App Flutter
            # Heatmap phân rã cổ phiếu
            heatmap_data = {
                "VN30_Bank": [
                    {"symbol": "VCB", "percent_change": 1.2, "value": 500000000},
                    {"symbol": "MBB", "percent_change": 0.8, "value": 400000000},
                    {"symbol": "TCB", "percent_change": -1.5, "value": 850000000}
                ],
                "Midcap_RealEstate": [
                    {"symbol": "DIG", "percent_change": 6.8, "value": 450000000},
                    {"symbol": "DXG", "percent_change": 4.1, "value": 300000000},
                    {"symbol": "PDR", "percent_change": 5.5, "value": 350000000}
                ],
                "Steel": [
                    {"symbol": "HPG", "percent_change": 2.4, "value": 1100000000},
                    {"symbol": "HSG", "percent_change": 1.2, "value": 250000000}
                ]
            }

            # Robot Quét Lực Nước Ngoài & Tự doanh
            foreign_flow = {
                "net_buy_value": -150000000, # Bán ròng 150 tỷ
                "top_buy": ["HPG", "FPT", "SSI"],
                "top_sell": ["VHM", "VNM", "MWG"]
            }

            return {
                "index": {
                    "VNINDEX": 1250.45,
                    "change": 8.5,
                    "percent_change": 0.68,
                    "volume": 850000000,
                    "value_billion_vnd": 21000 
                },
                "heatmap": heatmap_data,
                "foreign_flow": foreign_flow,
                "status": "success"
            }
        except Exception as e:
            print(f"Market Overview Error: {e}")
            return {"error": str(e)}

market_service = MarketService()
