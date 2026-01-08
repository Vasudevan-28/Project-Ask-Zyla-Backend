import os
import firebase_admin
from firebase_admin import credentials
import logging
import json
import base64

from dotenv import load_dotenv

load_dotenv()

# firebase_config_json = os.getenv("FIREBASE_CONFIG")

firebase_initialized = False

b64 = os.getenv("FIREBASE_CONFIG_BASE64")

decoded = base64.b64decode(b64).decode("utf-8")
config = json.loads(decoded)

try:
    # if os.path.exists(FIREBASE_KEY_PATH):
    # firebase_config = json.loads(confi)
    # cred = credentials.Certificate("firebase-service-key.json")
    cred = credentials.Certificate(config)
    firebase_admin.initialize_app(cred)
    firebase_initialized = True
    print("FIREBASE INITIALIZED SUCCESSFULLLYYYY")
        # _logger.info("Firebase Admin initialized from %s", FIREBASE_KEY_PATH)
    # else:
    #     _logger.warning("Firebase key file not found at '%s'. Firebase-dependent endpoints will fail until you provide it.", FIREBASE_KEY_PATH)
except Exception as exc:
    # If firebase admin fails to init, we capture the exception and continue;
    # endpoints that require Firebase should handle this case and return errors.
    # _logger.exception("Failed to initialize Firebase Admin SDK: %s", exc)
    firebase_initialized = False
