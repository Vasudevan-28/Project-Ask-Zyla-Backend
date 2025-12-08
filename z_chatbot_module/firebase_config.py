import firebase_admin
from firebase_admin import credentials

# Point this to your downloaded serviceAccountKey.json
cred = credentials.Certificate("firebase-service-key.json")

# Initialize Firebase Admin
firebase_admin.initialize_app(cred)
