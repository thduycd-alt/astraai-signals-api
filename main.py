from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import analyze, intraday, chat, market, comments, alerts
from services.notification_service import router as notifications_router

app = FastAPI(
    title="AstraAI Signals API",
    description="Backend AI phân tích chứng khoán đa tầng (7 Layers) và Radar Toàn Cảnh Đại Cục (Market Dashboard)",
    version="2.0.0"
)

# CORS setup cho Flutter Web/Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Các Module Endpoint Trung Tâm 
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["1. 7-Layer Analysis"])
app.include_router(intraday.router, prefix="/api/v1/intraday", tags=["2. Intraday Signals"])
app.include_router(market.router, prefix="/api/v1/market", tags=["3. Market Overview & Rotation"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["4. Chatbot AI"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["5. Social Comments"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["6. Shark Alerts"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["7. Push Notifications"])

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "AstraAI Signals V2.0 (With Sector Rotation) is running.",
        "docs": "/docs"
    }

@app.get("/debug/financial/{symbol}")
async def debug_financial(symbol: str):
    """Debug endpoint: xem raw columns của financial_ratio và income_statement cho symbol."""
    import traceback
    result = {}
    symbol = symbol.upper()

    try:
        from vnstock import financial_ratio
        df = financial_ratio(symbol, 'yearly', True)
        if df is not None and not df.empty:
            result['fr_yearly_cols'] = list(df.columns)
            result['fr_yearly_rows'] = df.head(2).to_dict(orient='records')
        else:
            result['fr_yearly_cols'] = []
    except Exception as e:
        result['fr_yearly_error'] = str(e)

    try:
        from vnstock import income_statement
        is_df = income_statement(symbol, 'yearly', True)
        if is_df is not None and not is_df.empty:
            result['is_yearly_cols'] = list(is_df.columns)
            result['is_yearly_rows'] = is_df.head(2).to_dict(orient='records')
        else:
            result['is_yearly_cols'] = []
    except Exception as e:
        result['is_yearly_error'] = str(e)

    # Chạy fundamental_service để xem yoy_growth thực tế
    try:
        from services.fundamental_service import fundamental_service
        data = fundamental_service.analyze(symbol, 16000)
        result['yoy_growth_pct'] = data.get('metrics', {}).get('yoy_growth_pct', 'NOT_FOUND')
        result['eps'] = data.get('metrics', {}).get('EPS', 'NOT_FOUND')
    except Exception as e:
        result['fundamental_error'] = str(e) + '\n' + traceback.format_exc()

    return result

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # CRITICAL: Tắt reload=True trên Production để tránh sập Server khi SQLite ghi file
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
