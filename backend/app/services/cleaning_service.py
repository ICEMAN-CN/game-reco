"""
数据清洗服务
"""
from app.cleaners.game_cleaner import GameCleaner

class CleaningService:
    """数据清洗服务"""
    
    def __init__(self):
        self.cleaner = GameCleaner()
    
    def clean_game_data(self, data: dict) -> dict:
        """清洗游戏数据"""
        return self.cleaner.clean(data)

