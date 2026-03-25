from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import os

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    symbol: str
    message: str
    history: List[ChatMessage] = []

@router.post("/")
async def chat_with_ai(prompt: ChatRequest):
    """
    Tích hợp Grok/Gemini API với Context là kết quả 7 tầng phân tích.
    Kiểm soát: 10 tin nhắn/giờ/user (Tránh lạm dụng token - Setup ở API Gateway/Middleware).
    """
    # Lấy API Key
    # gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # --- Blueprint RAG Flow ---
    # 1. Gọi Class ScoringService/Analyze để lấy TOÀN BỘ JSON Context 7 tầng.
    # 2. Xây dựng System Prompt: "Bạn là AstraAI, Tín hiệu Kỹ thuật = 80, CMF đang Mua Gom..."
    # 3. Request lên Grok / Gemini qua HTTPs.
    # 4. Return text response.

    # Mock Response for MVP
    mock_response = (f"AI đang phân tích câu hỏi của bạn về mã {prompt.symbol.upper()}... "
                     f"\nDựa vào dữ liệu hệ thống (Dòng tiền mua gom = {prompt.symbol.upper()}, "
                     "Vĩ mô ổn định), Khuyến nghị hiện tại là có thể nắm giữ 30% tỷ trọng.")

    return {
        "symbol": prompt.symbol.upper(),
        "status": "success",
        "response": mock_response
    }
