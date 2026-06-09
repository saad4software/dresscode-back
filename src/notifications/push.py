import logging
from typing import Any

from src.core.config import config

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _ensure_firebase() -> bool:
    global _firebase_initialized
    if not config.fcm_enabled:
        return False
    if not config.fcm_credentials_path:
        logger.warning("FCM enabled but FCM_CREDENTIALS_PATH is not set")
        return False
    if _firebase_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(config.fcm_credentials_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK")
        return False


def send_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> list[str]:
    """Send FCM push to tokens. Returns tokens that should be pruned."""
    if not tokens:
        return []
    if not _ensure_firebase():
        logger.info("FCM push skipped (disabled or not configured): %s", title)
        return []

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
    except Exception:
        logger.exception("FCM multicast send failed")
        return []

    invalid_tokens: list[str] = []
    for idx, send_response in enumerate(response.responses):
        if send_response.success:
            continue
        error = send_response.exception
        if error is None:
            continue
        code = getattr(error, "code", None)
        if code in ("NOT_FOUND", "UNREGISTERED", "INVALID_ARGUMENT"):
            invalid_tokens.append(tokens[idx])
        else:
            logger.warning("FCM send failed for token index %s: %s", idx, error)
    return invalid_tokens
