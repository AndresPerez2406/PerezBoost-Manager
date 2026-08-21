from sqlalchemy import Column, String
from backend.core.database import Base

class SistemaConfig(Base):
    __tablename__ = "sistema_config"

    clave = Column(String(255), primary_key=True, index=True)
    valor = Column(String, nullable=True)
