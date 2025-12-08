from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Profile(BaseModel):
    name: Optional[str] = None
    skin_type: Optional[str] = None
    concerns: List[str] = []
    allergies: List[str] = []
    avoid_ingredients: List[str] = []
    prefer_ingredients: List[str] = []
    budget_max: Optional[float] = None
    fragrance_free: Optional[bool] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = "New chat"

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    
class TrialChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    intent_query : str
    hits: List[Dict[str, Any]] =  Field(default_factory=list)
    intent_recommend: bool
    used_messages: List[Dict[str, Any]]
    profile_used: Profile
    summary: str
    user_profile : Dict[str, Any]
    
class TrialChatResponse(BaseModel):
    conversation_id: str
    remaining_trials: int
    reply : str
    trials_exhausted: bool
    
class TrialUserChkResponse(BaseModel):
    guest_id: str
    remaining_trials: int
    trials_exhausted: bool

class ProfilePatch(BaseModel):
    name: Optional[str] = None
    skin_type: Optional[str] = None
    concerns: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    avoid_ingredients: Optional[List[str]] = None
    prefer_ingredients: Optional[List[str]] = None
    budget_max: Optional[float] = None
    fragrance_free: Optional[bool] = None


class Favourites(BaseModel):
    # id  : Optional[str] = None
    product_name : str
    url : str
    category : str
    price : str
    clean_ingreds : List[str]
    
class SkinProfileWrapper1(BaseModel):
    skinProfileData: dict


class Allergies(BaseModel):
    hasAllergies: bool
    details: Optional[str] = ""

class MenstrualCycle(BaseModel):
    hasMenstrualCycle: bool
    nextCycle: Optional[str] = None
    skinBehavior: Optional[str] = None
    reminders: Optional[bool] = None

class OtherSymptoms(BaseModel):
    hasSymptoms: bool
    details: Optional[str] = ""

class SkinProfileData(BaseModel):
    userId: str
   
    concerns: List[str]
    skinType: List[str]
    skincareRoutine: str
    allergies: Allergies
    goals: List[str]
    menstrualCycle: MenstrualCycle
    otherSymptoms: OtherSymptoms

class SkinProfileWrapper(BaseModel):
    skinProfileData: SkinProfileData

    
    
    
"""
    Profile
    ProfilePatch
    ConversationCreate
    ChatRequest
    ChatResponse
    Favorites
"""