from typing import Optional
from pydantic import BaseModel 

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class FeedbackUpdate(BaseModel):
    name: str
    feedback: str

class RatingUpdate(BaseModel):
    rating: int

class SupportUpdate(BaseModel):
    message: str
    
class GenSupport(BaseModel):
    name: str
    email: str
    message: str
    
class FeedbackSubmit(BaseModel):
    emotion : int
    emotionLabel : str