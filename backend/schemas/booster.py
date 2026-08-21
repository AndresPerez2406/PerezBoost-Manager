from pydantic import BaseModel
from typing import Optional

class BoosterBase(BaseModel):
    nombre: str
    binance: Optional[str] = ""
    discord_id: Optional[str] = ""
    en_ranking: Optional[int] = 1

class BoosterCreate(BoosterBase):
    password: Optional[str] = "1234"

class BoosterUpdate(BaseModel):
    nombre: Optional[str] = None
    binance: Optional[str] = None
    discord_id: Optional[str] = None
    password: Optional[str] = None
    en_ranking: Optional[int] = None

class BoosterResponse(BoosterBase):
    id: int

    class Config:
        from_attributes = True
