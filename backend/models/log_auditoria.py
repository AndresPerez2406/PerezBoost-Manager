from sqlalchemy import Column, Integer, String
from backend.core.database import Base

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(String)
    evento = Column(String(100), index=True)
    detalles = Column(String)
