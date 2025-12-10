import os
from redis.asyncio import from_url

from dotenv import load_dotenv


REDIS_URL = os.getenv("REDIS_URL")
redis = from_url(REDIS_URL, decode_responses=True)


