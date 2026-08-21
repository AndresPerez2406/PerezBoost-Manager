from pydantic import BaseModel
from typing import Optional, List

class CuentaCreate(BaseModel):
    user_pass: str
    elo_tipo: str
    descripcion: Optional[str] = "FRESH"

class CuentaUpdate(BaseModel):
    user_pass: Optional[str] = None
    elo_tipo: Optional[str] = None
    descripcion: Optional[str] = None

class CuentaResponse(BaseModel):
    id: int
    user_pass: str
    elo_tipo: Optional[str] = None
    descripcion: Optional[str] = "FRESH"

    class Config:
        from_attributes = True

class LoteCuentasCreate(BaseModel):
    cuentas: List[str]
    elo_tipo: str
    descripcion: Optional[str] = "FRESH"
