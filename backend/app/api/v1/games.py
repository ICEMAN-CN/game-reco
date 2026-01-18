"""
游戏相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.game_service import GameService
from app.schemas.game import GameResponse, GameListResponse

router = APIRouter()
game_service = GameService()


@router.get("/games", response_model=GameListResponse)
async def get_games(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    db: Session = Depends(get_db)
):
    """获取游戏列表"""
    skip = (page - 1) * page_size
    games, total = game_service.get_games(
        db=db,
        skip=skip,
        limit=page_size,
        search=search,
        platform=platform,
        tag=tag
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return GameListResponse(
        items=[GameResponse.model_validate(game) for game in games],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(game_id: int, db: Session = Depends(get_db)):
    """获取游戏详情"""
    game = game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    return GameResponse.model_validate(game)

