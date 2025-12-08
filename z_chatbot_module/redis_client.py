import os
from redis.asyncio import from_url

from dotenv import load_dotenv


REDIS_URL = os.getenv("REDIS_URL")
# redis = from_url(REDIS_URL, decode_responses=True)
redis = from_url("redis://default:YKNjZUNO0cmDuGHYiszYf2y1lNuBUhe6@redis-19100.c114.us-east-1-4.ec2.cloud.redislabs.com:19100", decode_responses=True)


