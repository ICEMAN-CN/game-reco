"""
推荐相关 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.game_service import GameService
from app.schemas.game import GameResponse

router = APIRouter()
game_service = GameService()


@router.get("/recommendations/random", response_model=List[GameResponse])
async def get_random_games(
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    db: Session = Depends(get_db)
):
    """获取随机游戏推荐"""
    games = game_service.get_random_games(db, limit=limit)
    return [GameResponse.model_validate(game) for game in games]

