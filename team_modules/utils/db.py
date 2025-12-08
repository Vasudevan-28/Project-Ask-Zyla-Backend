from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # Load MongoDB URI from .env file

# MONGO_URI = os.getenv("MONGO_URI")

MONGO_URI = "mongodb+srv://saravanan_db:Saravanan@cluster0.2r4wahi.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)

db = client["auth_flow"]    # database name
users_col = db["users"]     # collection name
