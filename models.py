from typing import Optional
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    linked_id: Optional[str] = None
