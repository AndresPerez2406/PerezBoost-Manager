from sqlalchemy import Column, Integer, String, Float
from backend.core.database import Base

class ConfigPrecio(Base):
    __tablename__ = "config_precios"

    division = Column(String(50), primary_key=True, index=True)
    precio_cliente = Column(Float, nullable=False)
    margen_perez = Column(Float, nullable=False)
    puntos = Column(Integer, default=2)
