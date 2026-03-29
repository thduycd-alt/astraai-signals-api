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

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # CRITICAL: Tắt reload=True trên Production để tránh sập Server khi SQLite ghi file
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
