from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

class UserProfile(BaseModel):
    name: str
    role: str
    discord_id: Optional[str] = None
    binance: Optional[str] = None
