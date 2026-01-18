"""
游戏服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.game import Game
from app.schemas.game import GameCreate, GameUpdate

class GameService:
    """游戏服务"""
    
    def get_game(self, db: Session, game_id: int) -> Optional[Game]:
        """获取游戏详情"""
        return db.query(Game).filter(Game.id == game_id).first()
    
    def get_game_by_external_id(self, db: Session, external_id: int) -> Optional[Game]:
        """根据外部数据源ID获取游戏"""
        return db.query(Game).filter(Game.external_id == external_id).first()
    
    def get_games(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        platform: Optional[str] = None,
        tag: Optional[str] = None
    ) -> tuple[List[Game], int]:
        """获取游戏列表"""
        query = db.query(Game)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    Game.title.ilike(f"%{search}%"),
                    Game.title_english.ilike(f"%{search}%"),
                    Game.description.ilike(f"%{search}%")
                )
            )
        
        # 平台筛选
        if platform:
            query = query.filter(Game.platforms.contains([platform]))
        
        # 标签筛选
        if tag:
            query = query.filter(Game.tags.contains([tag]))
        
        # 总数
        total = query.count()
        
        # 分页
        games = query.order_by(Game.created_at.desc()).offset(skip).limit(limit).all()
        
        return games, total
    
    def get_random_games(self, db: Session, limit: int = 10) -> List[Game]:
        """获取随机游戏"""
        return db.query(Game).order_by(func.random()).limit(limit).all()
    
    def create_game(self, db: Session, game: GameCreate) -> Game:
        """创建游戏"""
        db_game = Game(**game.dict())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
        return db_game
    
    def update_game(self, db: Session, game_id: int, game: GameUpdate) -> Optional[Game]:
        """更新游戏"""
        db_game = self.get_game(db, game_id)
        if not db_game:
            return None
        
        update_data = game.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_game, key, value)
        
        db.commit()
        db.refresh(db_game)
        return db_game

