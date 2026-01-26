from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class SkinProfileWrapper1(BaseModel):
    skinProfileData: dict


class Allergies(BaseModel):
    hasAllergies: bool
    details: Optional[str] = ""


class MenstrualCycle(BaseModel):
    hasMenstrualCycle: bool
    nextCycle: Optional[str] = None
    skinBehavior: List[str] = []    
    reminders: Optional[bool] = None

class OtherSymptoms(BaseModel):
    hasSymptoms: bool
    details: Optional[str] = ""

class SkinProfileData(BaseModel):
    # userId: str
   
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