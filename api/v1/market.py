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

@router.get("/quotes")
async def get_quotes(symbols: str = ""):
    """
    Kéo giá Live cho nguyên 1 dàn Watchlist. Vd: ?symbols=HPG,VND,SSI
    """
    if not symbols: return {}
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return market_service.get_watchlist_quotes(sym_list)

@router.get("/index-candles")
async def get_index_candles(index: str = "VNINDEX", days: int = 60):
    """
    Kéo dữ liệu nến ngày của chỉ số: VNINDEX, HNXINDEX, UPCOMINDEX.
    Dùng cho biểu đồ nến chỉ số ở màn hình Toàn Cảnh.
    """
    allowed = {"VNINDEX", "HNXINDEX", "UPCOMINDEX", "HNXINDEX", "VN30", "HNXINDEX", "UPCOM", "HNXUPCOMINDEX"}
    idx_map = {"HNXINDEX": "HNXINDEX", "UPCOM": "UPCOMINDEX", "VN30": "VN30", "UPCOMINDEX": "UPCOMINDEX"}
    idx = index.upper()
    if idx not in allowed:
        idx = "VNINDEX"
    return {
        "index":   idx,
        "candles": market_service.get_index_candles(idx, min(days, 120))
    }
