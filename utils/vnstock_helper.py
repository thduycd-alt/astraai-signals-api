from vnstock import stock_historical_data
import pandas as pd
from datetime import datetime, timedelta

class VnstockHelper:
    """
    Helper module giao tiếp với thư viện vnstock để kéo dữ liệu chứng khoán VN.
    Cung cấp dữ liệu Lịch sử (Daily) và Intraday siêu nhỏ (1m, 3m, 5m).
    """
    
    @staticmethod
    def get_historical_data(symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Kéo dữ liệu EOD (End of Day) lịch sử Daily.
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            # vnstock API: resolution "1D" cho Daily
            df = stock_historical_data(symbol, start_date, end_date, "1D", "stock")
            if df is not None and not df.empty:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_intraday_data(symbol: str, timeframe: str = "1m", days_back: int = 5) -> pd.DataFrame:
        """
        Kéo dữ liệu Intraday siêu nhỏ. 
        Tham số timeframe: '1m', '3m', '5m'.
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d') 
        
        try:
            # Map timeframe sang tham số resolution của vnstock
            resolution_map = {"1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30", "1H": "1H", "1D": "1D"}
            res = resolution_map.get(timeframe, "1")
            
            df = stock_historical_data(symbol, start_date, end_date, res, "stock")
            if df is not None and not df.empty:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()

# Khởi tạo instance kết nối duy nhất
vnstock_client = VnstockHelper()
