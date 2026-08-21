from pydantic import BaseModel
from typing import Optional

class TarifaBase(BaseModel):
    division: str
    precio_cliente: float
    margen_perez: float
    puntos: Optional[int] = 2

class TarifaCreate(TarifaBase):
    pass

class TarifaUpdate(BaseModel):
    precio_cliente: Optional[float] = None
    margen_perez: Optional[float] = None
    puntos: Optional[int] = None

class TarifaResponse(TarifaBase):
    class Config:
        from_attributes = True
