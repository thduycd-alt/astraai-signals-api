from fastapi import APIRouter, Query

router = APIRouter()

from utils.vnstock_helper import vnstock_client
import math

@router.get("/{symbol}")
async def get_intraday_chart(symbol: str, timeframe: str = Query("1m", pattern="^(1m|3m|5m)$")):
    """
    Cung cấp dữ liệu Nến (OHLCV) Realtime từng phút cho Flutter Chart vẽ động (Live).
    """
    symbol = symbol.upper()
    df = vnstock_client.get_intraday_data(symbol, timeframe, days_back=2)
    
    if df.empty:
        return {"symbol": symbol, "status": "error", "message": "No intraday data", "data": []}
    
    if df.index.name == 'time':
        df = df.reset_index()
        
    df['time'] = df['time'].dt.strftime('%H:%M %d/%m')
    
    # Lọc 100 nến phút gần nhất để biểu đồ trên Mobile chạy mượt mà không bị kẹt bộ nhớ
    recent_df = df.tail(100)
    
    chart_data = []
    for _, row in recent_df.iterrows():
        # Clean data replacing NaN with 0 or previous val
        o = float(row['open']) if not math.isnan(row['open']) else 0.0
        h = float(row['high']) if not math.isnan(row['high']) else o
        l = float(row['low']) if not math.isnan(row['low']) else o
        c = float(row['close']) if not math.isnan(row['close']) else o
        v = int(row['volume']) if not math.isnan(row['volume']) else 0
        
        chart_data.append({
            "time": row['time'],
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v
        })

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "status": "success",
        "data": chart_data
    }
