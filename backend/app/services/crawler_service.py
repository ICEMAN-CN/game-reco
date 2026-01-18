"""
爬虫服务
"""
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable
from sqlalchemy.orm import Session
from decimal import Decimal
from app.crawlers.game_data_crawler import GameDataCrawler
from app.models.game import Game
from app.models.game_price import GamePrice
from app.models.game_rank_relation import GameRankRelation
from app.models.game_media_score import GameMediaScore
from app.models.review import Review
from app.config import settings

logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class CrawlerService:
    """爬虫服务"""
    
    def __init__(self):
        self.crawler = GameDataCrawler()
        # 缓存表存在性检查结果
        self._tables_cache = None
    
    async def crawl_and_save(
        self,
        db: Session,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> int:
        """
        抓取并保存游戏数据
        
        Args:
            db: 数据库会话
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            保存的游戏数量
        """
        try:
            # 抓取数据
            games_data = await self.crawler.fetch_games(limit=limit, offset=offset)
            logger.info(f"抓取到 {len(games_data)} 条游戏数据")
            
            saved_count = 0
            for game_data in games_data:
                try:
                    # 解析数据
                    parsed_data = self.crawler.parse_game_data({
                        "gameInfo": game_data.get("game_info"),
                        "raw_data": game_data.get("raw_data")
                    })
                    
                    # 检查是否已存在
                    existing = db.query(Game).filter(
                        Game.external_id == parsed_data["external_id"]
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        for key, value in parsed_data.items():
                            if key != "external_id":
                                setattr(existing, key, value)
                        db.commit()
                        logger.debug(f"更新游戏: {parsed_data['title']}")
                    else:
                        # 创建新记录
                        # 转换 Decimal 类型
                        from decimal import Decimal
                        for key in ["user_score", "price", "price_original", "steam_praise_rate"]:
                            if key in parsed_data and parsed_data[key] is not None:
                                parsed_data[key] = Decimal(str(parsed_data[key]))
                        
                        game = Game(**parsed_data)
                        db.add(game)
                        db.commit()
                        saved_count += 1
                        logger.debug(f"保存游戏: {parsed_data['title']}")
                        
                except Exception as e:
                    logger.error(f"处理游戏数据失败: {str(e)}")
                    db.rollback()
                    continue
            
            return saved_count
            
        except Exception as e:
            logger.error(f"抓取数据失败: {str(e)}")
            raise
        finally:
            await self.crawler.close()
    
    async def crawl_all(self, db: Session) -> int:
        """抓取所有数据"""
        total_saved = 0
        offset = 0
        batch_size = 100
        
        while True:
            saved = await self.crawl_and_save(db, limit=batch_size, offset=offset)
            if saved == 0:
                break
            total_saved += saved
            offset += batch_size
        
        return total_saved
    
    def save_rank_data_to_json(self, rank_id: int, data: dict) -> Path:
        """
        保存榜单数据到JSON文件
        
        Args:
            rank_id: 榜单ID
            data: 榜单数据
            
        Returns:
            保存的文件路径
        """
        file_path = DATA_DIR / f"rank_{rank_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存榜单数据到: {file_path}")
        return file_path
    
    def load_rank_data_from_json(self, rank_id: int) -> Optional[dict]:
        """
        从JSON文件加载榜单数据
        
        Args:
            rank_id: 榜单ID
            
        Returns:
            榜单数据，如果文件不存在返回None
        """
        file_path = DATA_DIR / f"rank_{rank_id}.json"
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"从文件加载榜单数据: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {str(e)}")
            return None
    
    async def crawl_all_ranks(self, rank_ids: List[int]) -> Dict[int, bool]:
        """
        批量抓取榜单数据，保存到JSON
        
        Args:
            rank_ids: 榜单ID列表
            
        Returns:
            每个rankId的抓取结果
        """
        results = {}
        total = len(rank_ids)
        
        print(f"\n{'='*60}")
        print(f"开始抓取 {total} 个榜单数据...")
        print(f"{'='*60}\n")
        
        for idx, rank_id in enumerate(rank_ids, 1):
            try:
                print(f"[{idx}/{total}] 正在抓取榜单 rankId={rank_id}...", end=" ", flush=True)
                data = await self.crawler.fetch_rank_games(rank_id)
                if data:
                    list_elements = data.get("listElements", [])
                    game_count = len(list_elements)
                    self.save_rank_data_to_json(rank_id, data)
                    results[rank_id] = True
                    print(f"✓ 成功 (获取 {game_count} 个游戏)")
                    logger.info(f"榜单 {rank_id} 抓取成功，获取 {game_count} 个游戏")
                else:
                    results[rank_id] = False
                    print(f"✗ 失败 (返回空数据)")
                    logger.warning(f"榜单 {rank_id} 返回空数据")
            except Exception as e:
                results[rank_id] = False
                print(f"✗ 失败 ({str(e)})")
                logger.error(f"抓取榜单 {rank_id} 失败: {str(e)}")
            
            # 添加延迟避免请求过快
            if idx < total:
                await asyncio.sleep(0.5)
        
        success_count = sum(1 for v in results.values() if v)
        print(f"\n{'='*60}")
        print(f"抓取完成: 成功 {success_count}/{total} 个榜单")
        print(f"{'='*60}\n")
        
        return results
    
    def load_and_parse_json_files(self, rank_ids: List[int]) -> List[Dict[str, Any]]:
        """
        从JSON文件加载并解析数据
        
        Args:
            rank_ids: 榜单ID列表
            
        Returns:
            解析后的游戏数据列表
        """
        all_games = {}
        total_ranks = len(rank_ids)
        
        print(f"\n开始解析 {total_ranks} 个榜单的JSON文件...")
        
        for idx, rank_id in enumerate(rank_ids, 1):
            print(f"[{idx}/{total_ranks}] 解析榜单 rankId={rank_id}...", end=" ", flush=True)
            data = self.load_rank_data_from_json(rank_id)
            if not data:
                print("✗ 文件不存在或加载失败")
                continue
            
            list_elements = data.get("listElements", [])
            parsed_count = 0
            for item in list_elements:
                try:
                    parsed = self.crawler.parse_rank_game_data(item)
                    game_id = parsed.get("external_id")
                    if game_id:
                        # 如果游戏已存在，合并数据
                        if game_id in all_games:
                            # 合并rank_id到关联列表
                            if "rank_ids" not in all_games[game_id]:
                                all_games[game_id]["rank_ids"] = []
                            if rank_id not in all_games[game_id]["rank_ids"]:
                                all_games[game_id]["rank_ids"].append(rank_id)
                        else:
                            parsed["rank_ids"] = [rank_id]
                            all_games[game_id] = parsed
                        parsed_count += 1
                except Exception as e:
                    logger.error(f"解析游戏数据失败: {str(e)}")
                    continue
            
            print(f"✓ 解析 {parsed_count} 个游戏")
        
        total_games = len(all_games)
        print(f"\n解析完成: 共 {total_games} 个唯一游戏\n")
        
        return list(all_games.values())
    
    async def fetch_game_details(self, game_id: int) -> Dict[str, Any]:
        """
        获取游戏详情（page和score API）
        
        Args:
            game_id: 游戏ID
            
        Returns:
            合并后的游戏详情
        """
        try:
            # 并发请求page和score API
            page_task = self.crawler.fetch_game_page(game_id)
            score_task = self.crawler.fetch_game_scores(game_id)
            
            page_data, score_data = await asyncio.gather(page_task, score_task, return_exceptions=True)
            
            # 处理异常
            if isinstance(page_data, Exception):
                logger.error(f"获取游戏详情失败 (game_id={game_id}): {page_data}")
                page_data = {}
            if isinstance(score_data, Exception):
                logger.error(f"获取游戏评分失败 (game_id={game_id}): {score_data}")
                score_data = {}
            
            # 解析数据
            parsed_page = self.crawler.parse_page_game_data(page_data) if page_data else {}
            parsed_score = self.crawler.parse_score_game_data(score_data) if score_data else {}
            
            # 合并数据
            merged = self.crawler.merge_game_data({}, parsed_page, parsed_score)
            return merged
            
        except Exception as e:
            logger.error(f"获取游戏详情失败 (game_id={game_id}): {str(e)}")
            return {}
    
    async def fetch_game_details_batch(
        self, 
        games_data: List[Dict[str, Any]], 
        concurrency: int = 5,
        delay_between_batches: float = 2.0,
        on_batch_complete: Optional[Callable[[List[Dict[str, Any]], int, int], Awaitable[None]]] = None
    ) -> None:
        """
        批量并行获取游戏详情
        
        Args:
            games_data: 游戏数据列表（会被原地更新）
            concurrency: 并发数，默认5
            delay_between_batches: 批次之间的延迟（秒），默认2秒
            on_batch_complete: 批次完成后的回调函数，参数为 (batch_games, batch_start, batch_end)
        """
        semaphore = asyncio.Semaphore(concurrency)
        total = len(games_data)
        completed = 0
        lock = asyncio.Lock()
        
        async def fetch_with_semaphore(game_data: Dict[str, Any], index: int):
            """带信号量控制的获取详情"""
            nonlocal completed
            async with semaphore:
                game_id = game_data.get("external_id")
                if not game_id:
                    async with lock:
                        completed += 1
                    return
                
                try:
                    details = await self.fetch_game_details(game_id)
                    if details:
                        game_data.update(details)
                    async with lock:
                        completed += 1
                        # 每10个打印一次进度
                        if completed % 10 == 0 or completed == total:
                            print(f"[{completed}/{total}] 已获取游戏详情: {game_id}")
                except Exception as e:
                    async with lock:
                        completed += 1
                    logger.error(f"获取游戏详情失败 (game_id={game_id}): {str(e)}")
        
        # 创建所有任务
        tasks = [
            fetch_with_semaphore(game_data, i)
            for i, game_data in enumerate(games_data)
        ]
        
        # 分批执行，批次之间延迟
        batch_size = concurrency
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_tasks = tasks[batch_start:batch_end]
            
            # 并发执行当前批次
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 批次完成回调
            if on_batch_complete:
                batch_games = games_data[batch_start:batch_end]
                if asyncio.iscoroutinefunction(on_batch_complete):
                    await on_batch_complete(batch_games, batch_start, batch_end)
                else:
                    on_batch_complete(batch_games, batch_start, batch_end)
            
            # 批次之间延迟
            if batch_end < total:
                print(f"批次完成 [{batch_start + 1}-{batch_end}/{total}]，等待 {delay_between_batches} 秒...")
                await asyncio.sleep(delay_between_batches)
    
    def save_games_to_db(self, db: Session, games_data: List[Dict[str, Any]], show_progress: bool = True) -> Dict[str, Any]:
        """
        批量写入games表
        
        Args:
            db: 数据库会话
            games_data: 游戏数据列表
            show_progress: 是否显示详细进度
            
        Returns:
            统计信息字典，包含：
            - saved_count: 新增游戏数
            - updated_count: 更新游戏数
            - failed_count: 失败数
            - relations_stats: 关联表统计
        """
        saved_count = 0
        updated_count = 0
        failed_count = 0
        total = len(games_data)
        relations_stats = {
            "rank_relations": 0,
            "prices": 0,
            "media_scores": 0,
            "reviews": 0
        }
        
        if show_progress:
            print(f"\n开始写入数据库 (共 {total} 个游戏)...")
            print(f"{'='*60}\n")
        
        for idx, game_data in enumerate(games_data, 1):
            try:
                external_id = game_data.get("external_id")
                if not external_id:
                    continue
                
                # 检查是否已存在
                existing = db.query(Game).filter(Game.external_id == external_id).first()
                
                # 准备数据
                game_dict = self._prepare_game_data(game_data)
                
                if existing:
                    # 更新现有记录
                    for key, value in game_dict.items():
                        if key != "external_id" and hasattr(existing, key):
                            setattr(existing, key, value)
                    db.commit()
                    game_id = existing.id
                    updated_count += 1
                    title = game_dict.get('title', f'ID:{external_id}')
                    if show_progress and (idx % 10 == 0 or idx == total):
                        print(f"[{idx}/{total}] 更新: {title}")
                    logger.debug(f"更新游戏: {title}")
                else:
                    # 创建新记录
                    game = Game(**game_dict)
                    db.add(game)
                    db.commit()
                    db.refresh(game)
                    game_id = game.id
                    saved_count += 1
                    title = game_dict.get('title', f'ID:{external_id}')
                    if show_progress and (idx % 10 == 0 or idx == total):
                        print(f"[{idx}/{total}] 新增: {title}")
                    logger.debug(f"保存游戏: {title}")
                
                # 保存关联数据（即使失败也不影响主游戏保存）
                try:
                    batch_relations_stats = self._save_game_relations(db, game_id, game_data)
                    # 累加统计
                    for key in relations_stats:
                        relations_stats[key] += batch_relations_stats.get(key, 0)
                except Exception as e:
                    logger.error(f"保存游戏关联数据失败 (game_id={game_id}): {str(e)}")
                    # 关联数据保存失败不影响主游戏，继续处理下一个
                
            except Exception as e:
                failed_count += 1
                logger.error(f"保存游戏数据失败: {str(e)}")
                db.rollback()
                if show_progress and (idx % 10 == 0 or idx == total):
                    print(f"[{idx}/{total}] ✗ 失败: {str(e)[:50]}")
                continue
        
        stats = {
            "saved_count": saved_count,
            "updated_count": updated_count,
            "failed_count": failed_count,
            "total": total,
            "relations_stats": relations_stats
        }
        
        if show_progress:
            print(f"\n{'='*60}")
            print(f"数据库写入完成:")
            print(f"  新增: {saved_count} 个游戏")
            print(f"  更新: {updated_count} 个游戏")
            print(f"  失败: {failed_count} 个游戏")
            print(f"  总计: {saved_count + updated_count}/{total}")
            print(f"  关联数据:")
            print(f"    - 榜单关联: {relations_stats['rank_relations']}")
            print(f"    - 价格信息: {relations_stats['prices']}")
            print(f"    - 媒体评分: {relations_stats['media_scores']}")
            print(f"    - 评论: {relations_stats['reviews']}")
            print(f"{'='*60}\n")
        
        return stats
    
    def _prepare_game_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备游戏数据，转换类型"""
        game_dict = {
            "external_id": data.get("external_id"),
            "title": data.get("title"),
            "title_english": data.get("title_english"),
            "developer_name": data.get("developer_name"),
            "publisher_name": data.get("publisher_name"),
            "description": data.get("description"),
            "description_html": data.get("description_html"),
            "cover_image_url": data.get("cover_image_url"),
            "thumbnail_url": data.get("thumbnail_url"),
            "horizontal_image_url": data.get("horizontal_image_url"),
            "platforms": data.get("platforms", []),
            "platform_ids": data.get("platform_ids", []),
            "tags": data.get("tags", []),
            "be_official_chinese_enable": data.get("be_official_chinese_enable"),
            "device_requirement_html": data.get("device_requirement_html"),
            "play_hours_caption": data.get("play_hours_caption"),
            "theme_color": data.get("theme_color"),
            "hot_value": data.get("hot_value"),
            "publish_date": data.get("publish_date"),
            "publish_timestamp": data.get("publish_timestamp"),
            "steam_game_id": data.get("steam_game_id"),
            "steam_header_image": data.get("steam_header_image"),
            "source": data.get("source", "external"),
            "raw_data": data.get("raw_data")
        }
        
        # 转换Decimal类型
        for key in ["user_score", "real_players_score", "price", "price_original", "steam_praise_rate"]:
            if key in data and data[key] is not None:
                try:
                    game_dict[key] = Decimal(str(data[key]))
                except (ValueError, TypeError):
                    logger.warning(f"无法转换 {key} 为 Decimal: {data[key]}")
                    game_dict[key] = None
        
        # 转换Integer类型
        for key in ["score_users_count", "playeds_count", "want_plays_count", "real_players_count"]:
            if key in data and data[key] is not None:
                try:
                    game_dict[key] = int(data[key])
                except (ValueError, TypeError):
                    logger.warning(f"无法转换 {key} 为 Integer: {data[key]}")
                    game_dict[key] = None
        
        # 转换Boolean类型
        if "is_free" in data:
            game_dict["is_free"] = bool(data["is_free"])
        
        # 转换BigInteger类型
        if "publish_timestamp" in data and data["publish_timestamp"] is not None:
            try:
                game_dict["publish_timestamp"] = int(data["publish_timestamp"])
            except (ValueError, TypeError):
                logger.warning(f"无法转换 publish_timestamp 为 BigInteger: {data['publish_timestamp']}")
                game_dict["publish_timestamp"] = None
        
        return game_dict
    
    def _get_tables(self, db: Session) -> set:
        """获取数据库表列表（带缓存）"""
        if self._tables_cache is None:
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            # 明确指定检查 public schema
            self._tables_cache = set(inspector.get_table_names(schema='public'))
        return self._tables_cache
    
    def _save_game_relations(self, db: Session, game_id: int, game_data: Dict[str, Any]) -> Dict[str, int]:
        """
        保存游戏关联数据
        
        Returns:
            统计信息字典，包含各表的写入数量
        """
        stats = {
            "rank_relations": 0,
            "prices": 0,
            "media_scores": 0,
            "reviews": 0
        }
        
        # 检查表是否存在（使用缓存）
        tables = self._get_tables(db)
        
        # 保存榜单关联
        if "game_rank_relations" in tables:
            rank_ids = game_data.get("rank_ids", [])
            for rank_id in rank_ids:
                try:
                    existing = db.query(GameRankRelation).filter(
                        GameRankRelation.game_id == game_id,
                        GameRankRelation.rank_id == rank_id
                    ).first()
                    if not existing:
                        relation = GameRankRelation(game_id=game_id, rank_id=rank_id)
                        db.add(relation)
                        stats["rank_relations"] += 1
                    db.commit()
                except Exception as e:
                    logger.error(f"保存榜单关联失败 (game_id={game_id}, rank_id={rank_id}): {str(e)}")
                    db.rollback()
        
        # 保存价格信息
        if "game_prices" in tables:
            price_infes = game_data.get("price_infes", [])
            for price_info in price_infes:
                try:
                    platform_name = price_info.get("platformName")
                    if not platform_name:
                        continue
                    
                    existing = db.query(GamePrice).filter(
                        GamePrice.game_id == game_id,
                        GamePrice.platform_name == platform_name
                    ).first()
                    
                    price_dict = {
                        "game_id": game_id,
                        "platform_name": platform_name,
                        "price": Decimal(str(price_info.get("price", 0))) if price_info.get("price") else None,
                        "price_lowest": Decimal(str(price_info.get("priceLowest", 0))) if price_info.get("priceLowest") else None,
                        "price_original": Decimal(str(price_info.get("priceOriginal", 0))) if price_info.get("priceOriginal") else None,
                        "sale_price_rate": Decimal(str(price_info.get("salePriceRate", 0))) if price_info.get("salePriceRate") else None,
                        "is_free": price_info.get("beFree", False)
                    }
                    
                    if existing:
                        for key, value in price_dict.items():
                            if key != "game_id" and key != "platform_name":
                                setattr(existing, key, value)
                    else:
                        price = GamePrice(**price_dict)
                        db.add(price)
                        stats["prices"] += 1
                    db.commit()
                except Exception as e:
                    logger.error(f"保存价格信息失败 (game_id={game_id}, platform={platform_name}): {str(e)}")
                    db.rollback()
        
        # 保存媒体评分
        if "game_media_scores" in tables:
            media_scores = game_data.get("media_scores", [])
            for media_score in media_scores:
                try:
                    media_name = media_score.get("media_name")
                    if not media_name:
                        continue
                    
                    existing = db.query(GameMediaScore).filter(
                        GameMediaScore.game_id == game_id,
                        GameMediaScore.media_name == media_name
                    ).first()
                    
                    score_dict = {
                        "game_id": game_id,
                        "media_name": media_name,
                        "score": Decimal(str(media_score.get("score", 0))) if media_score.get("score") else None,
                        "total_score": Decimal(str(media_score.get("total_score", 0))) if media_score.get("total_score") else None,
                        "content_url": media_score.get("content_url")
                    }
                    
                    if existing:
                        for key, value in score_dict.items():
                            if key != "game_id" and key != "media_name":
                                setattr(existing, key, value)
                    else:
                        score = GameMediaScore(**score_dict)
                        db.add(score)
                        stats["media_scores"] += 1
                    db.commit()
                except Exception as e:
                    logger.error(f"保存媒体评分失败 (game_id={game_id}, media={media_name}): {str(e)}")
                    db.rollback()
        
        # 保存评论
        if "reviews" in tables:
            reviews = game_data.get("reviews", [])
            for review_data in reviews:
                try:
                    comment_id = review_data.get("external_comment_id")
                    if not comment_id:
                        continue
                    
                    existing = db.query(Review).filter(
                        Review.external_comment_id == comment_id
                    ).first()
                    
                    review_dict = {
                        "game_id": game_id,
                        "external_comment_id": comment_id,
                        "ordernum": review_data.get("ordernum"),
                        "content": review_data.get("content"),
                        "content_html": review_data.get("content_html"),
                        "rating": Decimal(str(review_data.get("rating", 0))) if review_data.get("rating") else None,
                        "publish_time": self._parse_publish_time(review_data.get("publish_time")),
                        "praises_count": review_data.get("praises_count", 0),
                        "replies_count": review_data.get("replies_count", 0),
                        "treads_count": review_data.get("treads_count", 0),
                        "game_label_platform_names": review_data.get("game_label_platform_names", []),
                        "content_user_label_type_names": review_data.get("content_user_label_type_names", []),
                        "author_user_id": review_data.get("author_user_id"),
                        "author_name": review_data.get("author_name"),
                        "author_head_image_url": review_data.get("author_head_image_url"),
                        "raw_data": review_data.get("raw_data")
                    }
                    
                    if existing:
                        for key, value in review_dict.items():
                            if key != "external_comment_id":
                                setattr(existing, key, value)
                    else:
                        review = Review(**review_dict)
                        db.add(review)
                        stats["reviews"] += 1
                    db.commit()
                except Exception as e:
                    logger.error(f"保存评论失败 (game_id={game_id}, comment_id={comment_id}): {str(e)}")
                    db.rollback()
        
        return stats
    
    def _parse_publish_time(self, time_str: Optional[str]):
        """解析发布时间字符串"""
        if not time_str:
            return None
        try:
            from datetime import datetime
            # 格式: "2025-03-07"
            return datetime.strptime(time_str, "%Y-%m-%d")
        except Exception:
            return None
    
    async def crawl_all_reviews(
        self, 
        db: Session, 
        concurrency: int = 5, 
        delay: float = 2.0,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        从 games 表读取所有游戏，抓取并保存所有 reviews
        
        Args:
            db: 数据库会话
            concurrency: 并发数，默认5
            delay: 批次之间的延迟（秒），默认2秒
            limit: 限制处理的游戏数量（用于测试），None 表示处理所有游戏
            
        Returns:
            统计信息字典，包含：
            - total_games: 总游戏数
            - success_count: 成功抓取的游戏数
            - failed_count: 失败的游戏数
            - total_reviews: 保存的评论总数
        """
        from sqlalchemy import text
        
        # 检查 reviews 表是否存在
        tables = self._get_tables(db)
        if "reviews" not in tables:
            logger.error("reviews 表不存在，请先执行 database/init/006_create_reviews_table.sql")
            return {
                "total_games": 0,
                "success_count": 0,
                "failed_count": 0,
                "total_reviews": 0
            }
        
        # 清理所有现有 reviews
        print("清理现有 reviews 数据...")
        try:
            db.execute(text("TRUNCATE TABLE reviews CASCADE"))
            db.commit()
            print("✓ 已清理所有 reviews")
        except Exception as e:
            logger.error(f"清理 reviews 失败: {str(e)}")
            db.rollback()
            return {
                "total_games": 0,
                "success_count": 0,
                "failed_count": 0,
                "total_reviews": 0
            }
        
        # 查询所有游戏
        query = db.query(Game)
        if limit:
            query = query.limit(limit)
        
        games = query.all()
        total_games = len(games)
        
        if total_games == 0:
            print("没有找到游戏数据")
            return {
                "total_games": 0,
                "success_count": 0,
                "failed_count": 0,
                "total_reviews": 0
            }
        
        print(f"\n开始抓取 reviews (共 {total_games} 个游戏)")
        print(f"并发数: {concurrency}, 批次延迟: {delay} 秒\n")
        
        semaphore = asyncio.Semaphore(concurrency)
        success_count = 0
        failed_count = 0
        total_reviews = 0
        completed = 0
        lock = asyncio.Lock()
        
        async def fetch_reviews_for_game(game: Game):
            """为单个游戏抓取 reviews"""
            nonlocal success_count, failed_count, total_reviews, completed
            
            async with semaphore:
                try:
                    # 调用 score API
                    score_data = await self.crawler.fetch_game_scores(game.external_id)
                    
                    if not score_data or score_data.get("code") != 0:
                        async with lock:
                            failed_count += 1
                            completed += 1
                        return
                    
                    # 解析 reviews
                    parsed_score = self.crawler.parse_score_game_data(score_data)
                    reviews = parsed_score.get("reviews", [])
                    
                    if not reviews:
                        async with lock:
                            success_count += 1
                            completed += 1
                        return
                    
                    # 保存 reviews
                    game_stats = self._save_game_relations(db, game.id, {"reviews": reviews})
                    saved_reviews = game_stats.get("reviews", 0)
                    
                    async with lock:
                        success_count += 1
                        total_reviews += saved_reviews
                        completed += 1
                        
                        # 每10个游戏打印一次进度
                        if completed % 10 == 0 or completed == total_games:
                            title_preview = game.title[:30] if game.title else 'N/A'
                            print(f"[{completed}/{total_games}] 游戏 {game.external_id} ({title_preview}) - 保存 {saved_reviews} 条评论")
                
                except Exception as e:
                    async with lock:
                        failed_count += 1
                        completed += 1
                    logger.error(f"抓取 reviews 失败 (game_id={game.id}, external_id={game.external_id}): {str(e)}")
        
        # 创建所有任务
        tasks = [fetch_reviews_for_game(game) for game in games]
        
        # 分批执行，批次之间延迟
        batch_size = concurrency
        for batch_start in range(0, total_games, batch_size):
            batch_end = min(batch_start + batch_size, total_games)
            batch_tasks = tasks[batch_start:batch_end]
            
            # 并发执行当前批次
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 批次之间延迟
            if batch_end < total_games:
                print(f"批次完成 [{batch_start + 1}-{batch_end}/{total_games}]，等待 {delay} 秒...")
                await asyncio.sleep(delay)
        
        return {
            "total_games": total_games,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_reviews": total_reviews
        }

