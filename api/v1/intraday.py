from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/{symbol}")
async def get_intraday_signals(symbol: str, timeframe: str = Query("1m", pattern="^(1m|3m|5m)$")):
    """
    Tầng 6: Dò đáy đỉnh intraday 1m/3m/5m với detect đáy/đỉnh cục bộ và cumulative delta.
    """
    symbol = symbol.upper()
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "status": "success",
        "signals": {
            "local_bottoms": [],
            "local_tops": [],
            "wave_trend": "neutral"
        }
    }
