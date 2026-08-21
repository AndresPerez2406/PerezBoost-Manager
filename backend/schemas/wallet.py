from pydantic import BaseModel
from typing import Optional

class TransaccionCreate(BaseModel):
    tipo: str        # INGRESO / RETIRO
    categoria: str   # NETO / BOTE
    monto: float
    descripcion: Optional[str] = ""

class TransaccionResponse(BaseModel):
    id: int
    fecha: Optional[str] = None
    tipo: str
    categoria: str
    monto: float
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

class WalletBalanceResponse(BaseModel):
    saldo_neto: float
    saldo_bote: float
    total_binance: float
