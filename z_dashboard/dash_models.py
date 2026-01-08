from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from typing import Optional, List, Annotated
from bson import ObjectId
import uuid
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class ProductModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    routine: str
    slot: int
    type: Optional[str] = ""
    name: str
    desc: Optional[str] = ""
    reminder_time : Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "routine": "morning",
                "slot": 1,
                "type": "Moisturizer",
                "name": "My Cream",
                "desc": "Apply gently",
            }
        },
    )

class ToDoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    uid: Optional[str] = Field(default=None, description="User UID that owns this todo")
    text: str
    checked: bool = False
    date: str  # ISO Date string YYYY-MM-DD

    # model_config = ConfigDict(
    #     populate_by_name=True,
    #     arbitrary_types_allowed=True,
    #     json_schema_extra={
    #         "example": {
    #             "uid": "7953f153-222f-428f-8cd0-5aa8354bedb9",
    #             "text": "Complete Morning Routine",
    #             "checked": False,
    #             "date": "2023-10-27",
    #         }
    #     },
    # )

# class StreakRecord(BaseModel):
#     id: Optional[PyObjectId] = Field(alias="_id", default=None)
#     date: str # YYYY-MM-DD
#     completed: bool = False
    
#     model_config = ConfigDict(
#         populate_by_name=True,
#         arbitrary_types_allowed=True,
#         json_schema_extra={
#             "example": {
#                 "date": "2023-10-27",
#                 "completed": True,
#             }
#         },
#     )
