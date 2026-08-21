from pydantic import BaseModel
from typing import Optional

class PedidoCreate(BaseModel):
    booster_id: Optional[int] = None
    booster_nombre: str
    id_cuenta: int
    user_pass: str
    elo_inicial: str
    fecha_limite: str

class PedidoFinalizar(BaseModel):
    elo_final: str
    wr: float
    pago_cliente: float
    pago_booster: float
    ajuste_valor: Optional[float] = 0.0
    bote_pedido: Optional[float] = 0.0
    bote_wr: Optional[float] = 0.0
    cuenta_ranking: Optional[int] = 1

class PedidoEstadoUpdate(BaseModel):
    estado: str  # "Terminado" o "En progreso"
    booster_nombre: Optional[str] = None
    elo_final: Optional[str] = None
    wr: Optional[float] = None
    pago_cliente: Optional[float] = None
    pago_booster: Optional[float] = None
    pago_realizado: Optional[int] = None
    fecha_fin_real: Optional[str] = None
    bote_pedido: Optional[float] = None
    bote_wr: Optional[float] = None
    cuenta_ranking: Optional[int] = None

class PedidoOpggUpdate(BaseModel):
    opgg: Optional[str] = None

class PedidoResponse(BaseModel):
    id: int
    booster_id: Optional[int] = None
    booster_nombre: Optional[str] = None
    user_pass: Optional[str] = None
    elo_inicial: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_limite: Optional[str] = None
    estado: str
    elo_final: Optional[str] = None
    wr: Optional[float] = None
    fecha_fin_real: Optional[str] = None
    pago_cliente: Optional[float] = 0.0
    pago_booster: Optional[float] = 0.0
    ganancia_empresa: Optional[float] = 0.0
    pago_realizado: Optional[int] = 0
    opgg: Optional[str] = None
    notas: Optional[str] = None
    bote_pedido: Optional[float] = 0.0
    bote_wr: Optional[float] = 0.0
    cuenta_ranking: Optional[int] = 1

    class Config:
        from_attributes = True
