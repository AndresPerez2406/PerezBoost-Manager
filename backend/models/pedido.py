from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.core.database import Base

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booster_id = Column(Integer, ForeignKey("boosters.id"), nullable=True)
    booster_nombre = Column(String(255), index=True)
    user_pass = Column(String(255))
    elo_inicial = Column(String(50))
    fecha_inicio = Column(String(50))
    fecha_limite = Column(String(50))
    estado = Column(String(50), default="En progreso", index=True)
    elo_final = Column(String(50), nullable=True)
    wr = Column(Float, nullable=True)
    fecha_fin_real = Column(String(50), nullable=True, index=True)
    pago_cliente = Column(Float, default=0.0)
    pago_booster = Column(Float, default=0.0)
    ganancia_empresa = Column(Float, default=0.0)
    ajuste_valor = Column(Float, default=0.0)
    pago_realizado = Column(Integer, default=0, index=True)
    opgg = Column(String, default="")
    notas = Column(String, default="FRESH")
    bote_pedido = Column(Float, default=0.0)
    bote_wr = Column(Float, default=0.0)
    cuenta_ranking = Column(Integer, default=1)
