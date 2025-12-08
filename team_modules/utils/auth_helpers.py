import bcrypt
import random
import datetime

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_otp():
    return random.randint(1000, 9999)

def otp_expiry():
    # 3 minutes expiry
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
