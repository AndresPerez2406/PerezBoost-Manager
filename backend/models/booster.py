from sqlalchemy import Column, Integer, String
from backend.core.database import Base

class Booster(Base):
    __tablename__ = "boosters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(255), unique=True, nullable=False, index=True)
    binance = Column(String, default="")
    en_ranking = Column(Integer, default=1)
    password = Column(String, default="1234")
    discord_id = Column(String, default="")
