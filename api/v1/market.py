from fastapi import APIRouter
from services.market_service import market_service
from services.sector_rotation_service import sector_rotation_service

router = APIRouter()

@router.get("/overview")
async def get_market_overview():
    """
    Cung cấp cục Data Toàn Cảnh cho App Flutter Dashboard: 
    VNIndex, Biểu Đồ Nhiệt (Heatmap), Tự doanh & Khối ngoại.
    """
    return market_service.get_overview()

@router.get("/rotation")
async def get_sector_rotation():
    """
    Endpoint độc quyền "Cảnh báo Lịch Trình Luân chuyển Dòng tiền ngành".
    Phát tín hiệu Alert và kích hoạt Firebase Push Notification Tức Thời cho nhà đầu tư.
    """
    return sector_rotation_service.detect_rotation()
