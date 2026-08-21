from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.dashboard import RankingLeaderboardResponse
from backend.services.ranking_service import obtener_leaderboard_mes

router = APIRouter(prefix="/ranking", tags=["Leaderboard & Ranking"])

@router.get("", response_model=RankingLeaderboardResponse)
def get_ranking_leaderboard(mes: Optional[str] = None, db: Session = Depends(get_db)):
    return obtener_leaderboard_mes(db, mes)
