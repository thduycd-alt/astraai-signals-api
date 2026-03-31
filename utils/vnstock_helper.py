import pandas as pd
from datetime import datetime, timedelta

class VnstockHelper:
    """
    Helper module giao tiếp với vnstock v2 (stock_historical_data, stock_intraday_data).
    Venv hiện tại chứa vnstock phiên bản 2.x với các hàm:
      stock_historical_data, stock_intraday_data, financial_ratio, ...
    """

    @staticmethod
    def get_historical_data(symbol: str, days: int = 365) -> pd.DataFrame:
        """Kéo dữ liệu EOD (End of Day) lịch sử Daily."""
        end_date   = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            from vnstock import stock_historical_data
            df = stock_historical_data(symbol, start_date, end_date, '1D', 'stock')
            if df is None or df.empty:
                print(f"[vnstock] get_historical_data({symbol}): empty response")
                return pd.DataFrame()

            df.columns = [c.lower() for c in df.columns]

            # Chuẩn hóa index thành datetime
            time_col = 'time' if 'time' in df.columns else df.columns[0]
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.set_index(time_col)
            df.index.name = 'time'
            df = df.sort_index()
            print(f"[vnstock] {symbol} daily OK — {len(df)} rows, last close={df.iloc[-1]['close']}")
            return df

        except Exception as e:
            print(f"[vnstock] get_historical_data({symbol}) ERROR: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_intraday_data(symbol: str, timeframe: str = "1m", days_back: int = 2) -> pd.DataFrame:
        """Kéo dữ liệu Intraday theo phút."""
        end_date   = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        resolution_map = {
            "1m": 1, "3m": 3, "5m": 5,
            "15m": 15, "30m": 30, "1H": 60, "1D": "1D"
        }
        res = resolution_map.get(timeframe, 1)


        try:
            from vnstock import stock_intraday_data
            df = stock_intraday_data(symbol, start_date, end_date, res, 'stock')
            if df is None or df.empty:
                print(f"[vnstock] intraday({symbol}): empty")
                return pd.DataFrame()

            df.columns = [c.lower() for c in df.columns]
            time_col = 'time' if 'time' in df.columns else df.columns[0]
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.set_index(time_col)
            df.index.name = 'time'
            df = df.sort_index()
            return df

        except ImportError:
            # Fallback: stock_historical_data với resolution ngắn
            try:
                from vnstock import stock_historical_data
                df = stock_historical_data(symbol, start_date, end_date, res, 'stock')
                if df is None or df.empty:
                    return pd.DataFrame()
                df.columns = [c.lower() for c in df.columns]
                time_col = 'time' if 'time' in df.columns else df.columns[0]
                df[time_col] = pd.to_datetime(df[time_col])
                df = df.set_index(time_col)
                df.index.name = 'time'
                return df.sort_index()
            except Exception as e2:
                print(f"[vnstock] intraday fallback({symbol}) ERROR: {e2}")
                return pd.DataFrame()
        except Exception as e:
            print(f"[vnstock] intraday({symbol}) ERROR: {e}")
            return pd.DataFrame()


# Khởi tạo instance kết nối duy nhất
vnstock_client = VnstockHelper()
