"""
AstraAI Push Notification Service (Phase 3: FCM)
Gui Push Notification khi:
  1. Sector rotation > 5% (dong tien luan chuyen)
  2. Whale activity (V4 Elite score > 80)
  3. Price Alert tu client (webhook trigger)

De su dung: them FIREBASE_CREDENTIALS_PATH vao Render env vars
va include trong sector_rotation_service.py
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# ── Firebase Admin Setup ──────────────────────────────
_fcm_app = None

def _init_firebase():
    global _fcm_app
    if _fcm_app is not None:
        return _fcm_app
    try:
        import firebase_admin
        from firebase_admin import credentials

        # Priority 1: Render Secret Files (khuyến nghị)
        secret_path = "/etc/secrets/firebase-credentials.json"
        # Priority 2: Env var FIREBASE_CREDENTIALS_JSON (JSON string)
        cred_json   = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
        # Priority 3: Custom path
        cred_path   = os.environ.get("FIREBASE_CREDENTIALS_PATH", "")

        if os.path.exists(secret_path):
            cred = credentials.Certificate(secret_path)
        elif cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            logger.warning("[FCM] No Firebase credentials found. Push notifications disabled.")
            return None

        _fcm_app = firebase_admin.initialize_app(cred)
        logger.info("[FCM] Firebase initialized successfully.")
        return _fcm_app
    except ImportError:
        logger.warning("[FCM] firebase-admin not installed. Run: pip install firebase-admin")
        return None
    except Exception as e:
        logger.warning(f"[FCM] Firebase init error: {e}")
        return None

# ── Send Notification ─────────────────────────────────
def send_push(title: str, body: str, data: dict = None, topic: str = "all_users") -> bool:
    """
    Gui push notification den tat ca subscribers cua topic.
    topic='all_users' la mac dinh (user subscribe qua Flutter).
    """
    try:
        app = _init_firebase()
        if app is None:
            return False
        from firebase_admin import messaging
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            topic=topic,
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                headers={"apns-priority": "10"},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default", badge=1),
                ),
            ),
        )
        messaging.send(msg, app=app)
        logger.info(f"[FCM] Sent: {title} → {body}")
        return True
    except Exception as e:
        logger.warning(f"[FCM] Send error: {e}")
        return False

# ── Pre-built Alert Templates ─────────────────────────
def alert_sector_rotation(from_sector: str, to_sector: str, strength_pct: float):
    return send_push(
        title="🔄 Luân Chuyển Dòng Tiền",
        body=f"Tiền rút khỏi {from_sector}, chảy vào {to_sector} (+{strength_pct:.0f}%). Cơ hội tốt!",
        data={"type": "sector_rotation", "from": from_sector, "to": to_sector},
        topic="market_alerts",
    )

def alert_whale_entry(symbol: str, compression_score: float, whale_style: str):
    return send_push(
        title=f"🐋 Cá Mập Vào: {symbol}",
        body=f"{whale_style} | Điểm nén: {compression_score:.0f}/100. Theo dõi ngay!",
        data={"type": "whale", "symbol": symbol},
        topic="whale_alerts",
    )

def alert_price_target(symbol: str, current_price: float, target: float, condition: str):
    cond_str = "đã tăng đến" if condition == "above" else "đã giảm đến"
    return send_push(
        title=f"🎯 Alert Giá: {symbol}",
        body=f"{symbol} {cond_str} {current_price/1000:.1f}k (mục tiêu: {target/1000:.1f}k)",
        data={"type": "price_alert", "symbol": symbol},
        topic=f"alert_{symbol}",
    )

# ── FastAPI endpoint ──────────────────────────────────
from fastapi import APIRouter

router = APIRouter()

from pydantic import BaseModel

class PushPayload(BaseModel):
    title: str
    body: str
    topic: str = "all_users"
    data: dict = {}

@router.post("/send")
async def send_notification(payload: PushPayload):
    ok = send_push(payload.title, payload.body, payload.data, payload.topic)
    return {"sent": ok}

@router.post("/subscribe")
async def subscribe_topic(token: str, topic: str = "all_users"):
    """Dang ky FCM token vao topic (goi tu Flutter client khi khoi dong app)."""
    try:
        app = _init_firebase()
        if app is None:
            return {"ok": False, "msg": "Firebase not configured"}
        from firebase_admin import messaging
        r = messaging.subscribe_to_topic([token], topic, app=app)
        return {"ok": True, "success": r.success_count, "fail": r.failure_count}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
