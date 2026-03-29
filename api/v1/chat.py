from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.gemini_service import gemini_service

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    symbol: str
    message: str
    history: List[ChatMessage] = []

@router.post("/")
async def chat_with_ai(req: ChatRequest):
    """
    AstraAI Chatbot RAG: Gemini voi full context 7-tang phan tich co phieu.
    """
    symbol = req.symbol.upper()

    # Lay context tu du lieu market
    context_str = ""
    try:
        from utils.vnstock_helper import vnstock_client
        from services.technical_service import technical_service
        from services.smart_money_service import smart_money_service

        df = vnstock_client.get_historical_data(symbol, days=60)
        if not df.empty:
            tech = technical_service.analyze(df.copy())
            sm   = smart_money_service.analyze(df.copy())
            c_price = float(df.iloc[-1]['close'])
            context_str = (
                f"Ma co phieu: {symbol} | Gia hien tai: {c_price:,.0f} VND\n"
                f"Diem ky thuat: {tech.get('score',50)}/100 | Trend: {tech.get('trend','')}\n"
                f"RSI: {tech.get('indicators',{}).get('rsi_14',50):.1f} | "
                f"MACD: {tech.get('indicators',{}).get('macd_status','')}\n"
                f"Smart Money: {sm.get('score',50)}/100 | OBV: {sm.get('obv_trend','')}\n"
            )
    except Exception as e:
        context_str = f"Du lieu thi truong tam thoi khong kha dung: {e}"

    # Lich su hoi thoai
    history_text = ""
    for msg in req.history[-6:]:
        label = "Nguoi dung" if msg.role == "user" else "AstraAI"
        history_text += f"\n{label}: {msg.content}"

    prompt = f"""Ban la AstraAI — tro ly phan tich chung khoan chuyen nghiep thi truong Viet Nam.
Phong cach: ngan gon, sac ben, chuyen gia. Uu tien so lieu cu the, tranh tra loi chung chung.
Su dung tieng Viet trong toan bo cau tra loi.

=== CONTEXT THI TRUONG: {symbol} ===
{context_str}

=== LICH SU HOI THOAI ===
{history_text if history_text else "(Bat dau hoi thoai moi)"}

Nguoi dung: {req.message}
AstraAI:"""

    try:
        if gemini_service.model is None:
            raise ValueError("GEMINI_API_KEY chua duoc cau hinh")
        response = gemini_service.model.generate_content(prompt).text.strip()
    except Exception as e:
        response = (
            f"Xin loi, AI dang ban xu ly. Vui long thu lai sau.\n"
            f"[Loi: {str(e)[:120]}]"
        )

    return {"symbol": symbol, "status": "success", "response": response}
