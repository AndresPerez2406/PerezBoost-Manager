from pydantic import BaseModel
from typing import List, Optional

class ResumenFinancieroResponse(BaseModel):
    mes: str
    pedidos_completados: int
    mi_neto: float
    pago_staff: float
    bote_ranking: float
    ventas_totales: float
    velocidad_media_dias: float

class RankingItemResponse(BaseModel):
    rango: int
    booster_nombre: str
    terminados: int
    high_wr: int
    abandonos: int
    score: float

class RankingLeaderboardResponse(BaseModel):
    mes: str
    bote_total: float
    meta_cumplida: bool
    pedidos_actuales: int
    ranking: List[RankingItemResponse]

class StaffAnalyticsItem(BaseModel):
    booster_nombre: str
    total_ganancia: float
    wr_promedio: float
    pedidos_completados: int
    tiempo_promedio_dias: float
