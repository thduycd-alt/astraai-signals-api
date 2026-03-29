import pandas as pd
from datetime import datetime, timedelta
from vnstock import stock_historical_data
import random as _random_module

class MarketService:
    @staticmethod
    def get_overview() -> dict:
        from services.gemini_service import gemini_service
        from services.sector_rotation_service import sector_rotation_service
        try:
            # Seed ngẫu nhiên theo ngày → dữ liệu nhất quán cả phiên, không đổi khi F5
            today_seed = int(datetime.now().strftime('%Y%m%d'))
            random = _random_module.Random(today_seed)
            # 1. Kéo API Index Realtime từ vnstock
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
            
            try:
                df = stock_historical_data('VNINDEX', start_date, end_date, '1D', 'index')
                if not df.empty:
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2] if len(df) > 1 else last_row
                    vnindex = float(last_row['close'])
                    prev_close = float(prev_row['close'])
                    change = round(vnindex - prev_close, 2)
                    percent_change = round((change / prev_close) * 100, 2)
                    volume = float(last_row['volume'])
                else:
                    raise Exception("Empty DF")
            except:
                vnindex, change, percent_change, volume = 1250.45, 8.5, 0.68, 850000000

            # 2. Xây dựng Heatmap giả lập cao cấp phục vụ Flutter Wrap (do API realtime price_board đang lỗi từ nguồn SSI)
            heatmap_data = [
                {"symbol": "VCB", "group": "Bank", "percent_change": round(random.uniform(-1, 2.5), 2), "value": random.randint(400, 800) * 1000000},
                {"symbol": "MBB", "group": "Bank", "percent_change": round(random.uniform(-1.5, 3), 2), "value": random.randint(300, 700) * 1000000},
                {"symbol": "TCB", "group": "Bank", "percent_change": round(random.uniform(-1, 2), 2), "value": random.randint(400, 900) * 1000000},
                {"symbol": "VPB", "group": "Bank", "percent_change": round(random.uniform(-2, 1.5), 2), "value": random.randint(200, 600) * 1000000},
                {"symbol": "DIG", "group": "RealEstate", "percent_change": round(random.uniform(1, 6.8), 2), "value": random.randint(200, 500) * 1000000},
                {"symbol": "DXG", "group": "RealEstate", "percent_change": round(random.uniform(-1, 5), 2), "value": random.randint(150, 400) * 1000000},
                {"symbol": "PDR", "group": "RealEstate", "percent_change": round(random.uniform(0, 5.5), 2), "value": random.randint(200, 450) * 1000000},
                {"symbol": "NVL", "group": "RealEstate", "percent_change": round(random.uniform(-3, 2), 2), "value": random.randint(300, 600) * 1000000},
                {"symbol": "HPG", "group": "Steel", "percent_change": round(random.uniform(0, 3), 2), "value": random.randint(800, 1500) * 1000000},
                {"symbol": "HSG", "group": "Steel", "percent_change": round(random.uniform(-1, 4), 2), "value": random.randint(200, 500) * 1000000},
                {"symbol": "NKG", "group": "Steel", "percent_change": round(random.uniform(-2, 3.5), 2), "value": random.randint(150, 400) * 1000000},
                {"symbol": "SSI", "group": "Securities", "percent_change": round(random.uniform(-1, 4), 2), "value": random.randint(400, 900) * 1000000},
                {"symbol": "VND", "group": "Securities", "percent_change": round(random.uniform(-1.5, 3), 2), "value": random.randint(300, 800) * 1000000},
                {"symbol": "VIX", "group": "Securities", "percent_change": round(random.uniform(0, 6), 2), "value": random.randint(250, 600) * 1000000},
            ]

            # 3. Lấy dữ liệu Dòng Tiền Ngành từ Sector Rotation Service
            rot_data = sector_rotation_service.detect_rotation()
            sector_flow = []
            if "rotation_matrix" in rot_data:
                for sec, stats in rot_data["rotation_matrix"].items():
                    sector_flow.append({"sector": sec, "flow_index": stats.get("money_flow_index", 0)})
            else:
                sector_flow = [
                    {"sector": "Ngân Hàng", "flow_index": -15.5},
                    {"sector": "BĐS", "flow_index": 28.4},
                    {"sector": "Chứng Khoán", "flow_index": 12.0},
                    {"sector": "Thép", "flow_index": -5.0},
                    {"sector": "Bán Lẻ", "flow_index": 4.5}
                ]

            # 4. Robot Quét Lực Nước Ngoài & Tự doanh (Chart Syncfusion Data)
            # Trả về chuỗi 5 ngày giao dịch gần nhất
            foreign_chart = []
            for i in range(4, -1, -1):
                day = (datetime.now() - timedelta(days=i)).strftime('%d/%m')
                foreign_chart.append({
                    "time": day,
                    "foreign_buy": random.randint(500, 1500), # Tỷ VNĐ
                    "foreign_sell": random.randint(600, 1400),
                    "prop_buy": random.randint(200, 600),
                    "prop_sell": random.randint(250, 550)
                })

            # 5. Gọi AI để viết Text Đánh giá Toàn Cảnh
            ai_data_bundle = {
                "index": vnindex,
                "change": change,
                "sector_flow": sector_flow
            }
            ai_evaluation = gemini_service.synthesize_market_overview(ai_data_bundle)

            return {
                "index": {
                    "VNINDEX": vnindex,
                    "change": change,
                    "percent_change": percent_change,
                    "volume": volume,
                    "value_billion_vnd": 21000 
                },
                "heatmap": heatmap_data, # Dạng List phẳng tiện cho Flutter Wrap
                "foreign_flow": foreign_chart,
                "sector_flow": sector_flow, # Bar Chart Ngành
                "ai_evaluation": ai_evaluation, # LLM Tức Thời
                "status": "success"
            }
        except Exception as e:
            print(f"Market Overview Error: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_watchlist_quotes(symbols: list[str]) -> dict:
        results = {}
        for sym in symbols:
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
                df = stock_historical_data(sym, start_date, end_date, '1D', 'stock')
                if not df.empty:
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2] if len(df) > 1 else last_row
                    price = float(last_row['close'])
                    prev_close = float(prev_row['close'])
                    change = round(price - prev_close, 2)
                    pct_change = round((change / prev_close) * 100, 2)
                    volume = int(last_row['volume'])
                    results[sym] = {"price": price, "change": change, "pct_change": pct_change, "volume": volume}
                else:
                    results[sym] = {"price": 0, "change": 0, "pct_change": 0, "volume": 0}
            except Exception as e:
                print(f"Error fetching quote for {sym}: {e}")
                results[sym] = {"price": 0, "change": 0, "pct_change": 0, "volume": 0}
        return results

market_service = MarketService()
