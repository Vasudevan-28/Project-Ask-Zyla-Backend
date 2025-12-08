# backend/utils/firebase_admin_init.py
import os
import firebase_admin
from firebase_admin import credentials
import logging

_logger = logging.getLogger("firebase_admin_init")

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

firebase_initialized = False

try:
    # if os.path.exists(FIREBASE_KEY_PATH):
    cred = credentials.Certificate("z_authentication_module/utils/firebase_key.json")
    firebase_admin.initialize_app(cred)
    firebase_initialized = True
        # _logger.info("Firebase Admin initialized from %s", FIREBASE_KEY_PATH)
    # else:
    #     _logger.warning("Firebase key file not found at '%s'. Firebase-dependent endpoints will fail until you provide it.", FIREBASE_KEY_PATH)
except Exception as exc:
    # If firebase admin fails to init, we capture the exception and continue;
    # endpoints that require Firebase should handle this case and return errors.
    _logger.exception("Failed to initialize Firebase Admin SDK: %s", exc)
    firebase_initialized = False
