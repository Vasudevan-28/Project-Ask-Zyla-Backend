from datetime import timezone
import pytz
from dateutil import parser

IST = pytz.timezone("Asia/Kolkata")

def make_tz_aware(dt):
    if dt is None:
        return None

    # If stored as string (ISO)
    if isinstance(dt, str):
        try:
            dt = parser.isoparse(dt)
        except Exception:
            return None

    # If naive, treat as UTC from Mongo and convert to IST
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST)