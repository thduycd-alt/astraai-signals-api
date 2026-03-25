from fastapi import APIRouter
import pandas as pd
from utils.vnstock_helper import vnstock_client
from services.technical_service import technical_service
from services.smart_money_service import smart_money_service
from services.fundamental_service import fundamental_service
from services.macro_service import macro_service
from services.news_rumor_service import news_rumor_service
from services.intraday_service import intraday_service
from services.scoring_service import scoring_service

router = APIRouter()

@router.get("/{symbol}")
async def analyze_stock(symbol: str):
    """
    Endpoint Core: Chắp nối kéo data từ vnstock và đẩy tuần tự qua 7 Tầng Phân Tích (7 Layers).
    """
    symbol = symbol.upper()
    
    # 1. Kéo dữ liệu Daily (365 ngày để test MA200)
    df_daily = vnstock_client.get_historical_data(symbol, days=365)
    
    # 2. Kéo dữ liệu Intraday 5m (để test dò đáy/đỉnh lớp 6)
    df_intraday = vnstock_client.get_intraday_data(symbol, timeframe="5m")
    
    # --- CHẠY 6 LAYER PHÂN TÍCH ĐỘC LẬP --- 
    
    # Layer 1 & 2 (Technical & Smart Money) - Cần Data Daily
    tech_data = technical_service.analyze(df_daily.copy() if not df_daily.empty else pd.DataFrame())
    sm_data = smart_money_service.analyze(df_daily.copy() if not df_daily.empty else pd.DataFrame())
    
    # Layer 3, 4, 5 (Cơ bản, Vĩ mô, Tin Tức Ngoại vi)
    fundamental_data = fundamental_service.analyze(symbol)
    macro_data = macro_service.analyze(symbol)
    news_data = news_rumor_service.analyze(symbol)
    
    # Layer 6 (Intraday Signals) - Cần Data Intraday
    intraday_data = intraday_service.analyze(df_intraday.copy() if not df_intraday.empty else pd.DataFrame())
    
    # --- LAYER 7: TỔNG HỢP SCORING ---
    layers_payload = {
        "technical": tech_data,
        "smart_money": sm_data,
        "fundamental": fundamental_data,
        "macro": macro_data,
        "news_rumor": news_data,
        "intraday": intraday_data
    }
    
    final_result = scoring_service.calculate_final(layers_payload)

    # Trả về JSON theo cấu trúc Flutter yêu cầu
    return {
        "symbol": symbol,
        "status": "success",
        "data": {
            "layers": layers_payload,
            "final_analysis": final_result
        }
    }
