from sqlalchemy import Column, Integer, String
from backend.core.database import Base

class Inventario(Base):
    __tablename__ = "inventario"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_pass = Column(String(255), unique=True, nullable=False, index=True)
    elo_tipo = Column(String(50), nullable=True)
    descripcion = Column(String, default="FRESH")
