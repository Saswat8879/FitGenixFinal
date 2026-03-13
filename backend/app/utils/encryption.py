from cryptography.fernet import Fernet, InvalidToken
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_fernet = None


def _get_fernet() -> Fernet | None:
    global _fernet
    if _fernet is None and settings.FERNET_KEY:
        try:
            _fernet = Fernet(settings.FERNET_KEY.encode())
        except Exception:
            logger.warning("Invalid FERNET_KEY. Token encryption disabled.")
    return _fernet


def encrypt_token(token: str) -> str:
    f = _get_fernet()
    if f is None:
        return token
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    f = _get_fernet()
    if f is None:
        return encrypted
    try:
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token — key may have changed.")
        return ""
