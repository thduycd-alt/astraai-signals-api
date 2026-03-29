
"""
Tầng 8 (MỚI): Lịch Sự Kiện Tài Chính (Financial Calendar)
Hiển thị các sự kiện quan trọng của doanh nghiệp:
- Ngày Đại Hội Cổ Đông (ĐHCĐ)
- Ngày Chốt Quyền Nhận Cổ Tức
- Ngày Công Bố Báo Cáo Tài Chính (BCTC Quý)
Các sự kiện này tác động cực mạnh đến giá cổ phiếu.
"""

import re
from datetime import datetime

# Bảng tra cứu sự kiện tĩnh (Blueprint) — sau này sẽ kết nối API TCBS/SSI
# Format: symbol -> list of events
FINANCIAL_EVENTS_DB = {
    "STB":  [
        {"event": "ĐHCĐ Thường niên 2025", "date": "2025-04-26", "impact": "high"},
        {"event": "BCTC Q1/2025", "date": "2025-04-30", "impact": "medium"},
        {"event": "Chốt quyền cổ tức", "date": "2025-06-15", "impact": "high"},
    ],
    "VCB":  [
        {"event": "ĐHCĐ 2025", "date": "2025-04-12", "impact": "high"},
        {"event": "BCTC Q1/2025", "date": "2025-04-28", "impact": "medium"},
    ],
    "MBB":  [
        {"event": "BCTC Q1/2025", "date": "2025-04-24", "impact": "medium"},
        {"event": "ĐHCĐ Bất thường", "date": "2025-05-15", "impact": "medium"},
    ],
    "HPG":  [
        {"event": "BCTC Q1/2025", "date": "2025-04-28", "impact": "medium"},
        {"event": "ĐHCĐ 2025", "date": "2025-04-19", "impact": "high"},
    ],
    "FPT":  [
        {"event": "BCTC Q1/2025", "date": "2025-04-25", "impact": "medium"},
        {"event": "Chốt quyền cổ tức", "date": "2025-05-23", "impact": "high"},
    ],
    "VHM":  [
        {"event": "ĐHCĐ 2025", "date": "2025-04-23", "impact": "high"},
    ],
    "TCB":  [
        {"event": "BCTC Q1/2025", "date": "2025-04-22", "impact": "medium"},
    ],
}


class FinancialCalendarService:
    """
    Tra cứu và trả về danh sách sự kiện tài chính quan trọng
    sắp tới trong vòng 60 ngày cho một mã cổ phiếu.
    """

    @staticmethod
    def get_upcoming_events(symbol: str) -> dict:
        symbol = symbol.upper()
        now = datetime.now()
        events = FINANCIAL_EVENTS_DB.get(symbol, [])
        
        upcoming = []
        for ev in events:
            try:
                ev_date = datetime.strptime(ev["date"], "%Y-%m-%d")
                days_until = (ev_date - now).days
                if -7 <= days_until <= 60:  # ±1 tuần rồi đến 60 ngày tới
                    upcoming.append({
                        "event": ev["event"],
                        "date": ev["date"],
                        "days_until": days_until,
                        "impact": ev["impact"],
                        "label": (
                            f"⚠️ {ev['event']} ({days_until} ngày nữa)" if days_until > 0
                            else f"✅ {ev['event']} (Hôm nay / Vừa xảy ra)"
                        )
                    })
            except:
                pass

        # Sắp xếp theo ngày gần nhất
        upcoming.sort(key=lambda x: x["days_until"])

        # Sinh cảnh báo nếu có sự kiện quan trọng trong 7 ngày
        alert = None
        imminent = [e for e in upcoming if 0 <= e["days_until"] <= 7 and e["impact"] == "high"]
        if imminent:
            ev = imminent[0]
            alert = f"📅 {ev['event']} sẽ diễn ra trong {ev['days_until']} ngày tới — chuẩn bị thanh khoản!"

        return {
            "symbol": symbol,
            "upcoming_events": upcoming,
            "alert": alert,
            "has_events": len(upcoming) > 0
        }


financial_calendar_service = FinancialCalendarService()
