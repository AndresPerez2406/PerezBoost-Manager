from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.core.database import Base

class WalletPerez(Base):
    __tablename__ = "wallet_perez"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    tipo = Column(String(50), nullable=False)        # INGRESO / RETIRO
    categoria = Column(String(50), nullable=False)   # NETO / BOTE
    monto = Column(Float, nullable=False)
    descripcion = Column(String, nullable=True)
