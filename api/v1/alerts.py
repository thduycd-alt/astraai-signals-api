from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/shark")
async def get_shark_alerts():
    """
    Quét liên tục các tín hiệu Lệnh Lớn/Tự doanh xả ròng bất thường trong 3 phút qua.
    Trong bản Alpha, hệ thống sẽ random giả lập tín hiệu để Frontend (Flutter) test Snackbars.
    """
    alerts = []
    
    # Điểm kích nổ giả lập (15% cơ hội ra tín hiệu mỗi lần gọi)
    if random.random() < 0.15:
        symbol = random.choice(["SSI", "HPG", "DIG", "VPB", "MWG", "VND", "TCB", "NVL", "PDR"])
        action = random.choice(["GOM RÒNG KHỦNG", "XẢ RÒNG ÁP ĐẢO"])
        color = "GREEN" if action == "GOM RÒNG KHỦNG" else "RED"
        volume = random.randint(500, 2500) * 1000 # 500k - 2.5tr cổ
        
        alerts.append({
            "id": random.randint(1000, 999999),
            "symbol": symbol,
            "title": f"CÁ MẬP {action} {symbol}",
            "message": f"Phát hiện chùm lệnh {action} {volume:,} cổ phiếu {symbol} trong 3 phút qua!",
            "level": "CRITICAL",
            "color": color
        })
        
    return {"alerts": alerts, "status": "success"}
