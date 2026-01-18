"""
游戏数据爬虫实现
支持从外部数据源获取游戏信息
"""
import httpx
import logging
import os
from typing import List, Dict, Any, Optional
from app.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class GameDataCrawler(BaseCrawler):
    """游戏数据爬虫 - 从外部数据源获取游戏信息"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        # 从环境变量获取配置，或使用默认值
        api_url = api_url or os.getenv("GAME_DATA_API_URL", "")
        super().__init__(api_url, api_key)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_headers = {
            "Accept": "*/*",
            "User-Agent": "GameOdyssey/1.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    
    async def fetch_games(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0,
        section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        抓取游戏数据
        
        Args:
            limit: 限制数量
            offset: 偏移量
            section: 时间段 (格式: "202507")
            
        Returns:
            游戏数据列表
        """
        games = []
        page = 0
        page_size = 20
        
        if not self.api_url:
            logger.warning("未配置数据源 API URL，请设置 GAME_DATA_API_URL 环境变量")
            return games
        
        try:
            while True:
                # 构建请求参数
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                if section:
                    params["section"] = section
                
                # 发送请求
                response = await self.client.get(
                    f"{self.api_url}/api/games",
                    params=params,
                    headers={"User-Agent": "Game-Odyssey/1.0"}
                )
                response.raise_for_status()
                data = response.json()
                
                # 解析响应
                if data.get("code") != 0:
                    logger.error(f"API 返回错误: {data.get('message')}")
                    break
                
                list_elements = data.get("data", {}).get("listElements", [])
                if not list_elements:
                    break
                
                # 提取游戏数据
                for element in list_elements:
                    if element.get("type") == "game_big_card_model":
                        game_info = element.get("gameInfo")
                        if game_info:
                            games.append({
                                "raw_data": element,
                                "game_info": game_info
                            })
                
                # 检查是否达到限制
                if limit and len(games) >= limit:
                    games = games[:limit]
                    break
                
                # 检查是否还有更多数据
                if len(list_elements) < page_size:
                    break
                
                page += 1
                
        except Exception as e:
            logger.error(f"抓取数据失败: {str(e)}")
            raise
        
        return games
    
    def parse_game_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析游戏数据
        从 gameInfo 字段提取结构化数据
        
        Args:
            raw_data: 原始数据 (包含 gameInfo)
            
        Returns:
            解析后的游戏数据
        """
        game_info = raw_data.get("gameInfo", {})
        element = raw_data.get("raw_data", {})
        
        # 提取基本信息
        parsed = {
            "external_id": game_info.get("id"),
            "title": game_info.get("title"),
            "title_english": game_info.get("titleInEnglish"),
            "developer_name": game_info.get("developerName"),
            "publisher_name": game_info.get("publisherName"),
            "description_html": game_info.get("detailInHtml"),
            "description": self._extract_text_from_html(game_info.get("detailInHtml", "")),
            "cover_image_url": game_info.get("coverImageUrl"),
            "thumbnail_url": game_info.get("thumbnailUrl"),
            "horizontal_image_url": game_info.get("horizontalImageUrl"),
            "platforms": game_info.get("devicePlatformNames", []),
            "platform_ids": game_info.get("devicePlatformIds", []),
            "tags": [tag.get("caption") for tag in game_info.get("tags", []) if tag.get("caption")],
        }
        
        # 提取发布时间
        publish_time = game_info.get("publishTime")
        if publish_time:
            parsed["publish_date"] = self._parse_date(publish_time.get("publishTime"))
            parsed["publish_timestamp"] = publish_time.get("publishTimeStamp")
        
        # 提取评分信息
        score_info = game_info.get("scoreInfo", {})
        if score_info:
            parsed["user_score"] = score_info.get("userScore")
            parsed["score_users_count"] = score_info.get("scoreUsersCount")
            parsed["playeds_count"] = score_info.get("playedsCount")
            parsed["want_plays_count"] = score_info.get("wantPlaysCount")
        
        # 提取 Steam 信息
        steam_info = game_info.get("steamInfo", {})
        if steam_info:
            parsed["steam_game_id"] = steam_info.get("gameId")
            parsed["steam_praise_rate"] = steam_info.get("praiseRate")
            parsed["steam_header_image"] = steam_info.get("steamHeaderImage")
        
        # 提取价格信息
        price_info = element.get("gamePriceInfo") or game_info.get("gamePriceInfo")
        if price_info:
            parsed["is_free"] = price_info.get("beFree", False)
            parsed["price"] = price_info.get("price")
            parsed["price_original"] = price_info.get("priceOriginal")
        
        # 提取配置要求
        parsed["device_requirement_html"] = game_info.get("deviceRequirementInHtml")
        
        # 保存原始数据
        parsed["raw_data"] = element
        parsed["source"] = "external"
        
        return parsed
    
    def _extract_text_from_html(self, html: str) -> str:
        """从 HTML 中提取纯文本"""
        if not html:
            return ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(strip=True)
        except Exception as e:
            logger.warning(f"HTML 解析失败: {str(e)}")
            return html
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # 格式: "2025-07-02T00:00:00+08:00"
            return date_str.split("T")[0]
        except Exception:
            return None
    
    async def fetch_rank_games(self, rank_id: int, page_size: int = 200, page_index: int = 0) -> Dict[str, Any]:
        """
        抓取榜单游戏列表
        
        Args:
            rank_id: 榜单ID
            page_size: 每页数量
            page_index: 页码
            
        Returns:
            榜单数据
        """
        if not self.api_url:
            logger.warning("未配置数据源 API URL")
            return {}
            
        try:
            url = f"{self.api_url}/rank"
            params = {
                "rankId": rank_id,
                "pageSize": page_size,
                "pageIndex": page_index
            }
            
            response = await self.client.get(url, params=params, headers=self.base_headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                logger.error(f"Rank API 返回错误: {data.get('error')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"抓取榜单数据失败 (rank_id={rank_id}): {str(e)}")
            raise
    
    async def fetch_game_page(self, game_id: int) -> Dict[str, Any]:
        """
        抓取游戏详情页
        
        Args:
            game_id: 游戏ID
            
        Returns:
            游戏详情数据
        """
        if not self.api_url:
            logger.warning("未配置数据源 API URL")
            return {}
            
        try:
            url = f"{self.api_url}/game/{game_id}"
            
            response = await self.client.get(url, headers=self.base_headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                logger.error(f"Page API 返回错误: {data.get('error')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"抓取游戏详情失败 (game_id={game_id}): {str(e)}")
            raise
    
    async def fetch_game_scores(self, game_id: int, page_size: int = 100, page_index: int = 0) -> Dict[str, Any]:
        """
        抓取游戏评分和评论
        
        Args:
            game_id: 游戏ID
            page_size: 每页评论数量
            page_index: 页码
            
        Returns:
            评分和评论数据
        """
        if not self.api_url:
            logger.warning("未配置数据源 API URL")
            return {}
            
        try:
            url = f"{self.api_url}/game/{game_id}/scores"
            payload = {
                "gameId": game_id,
                "pageIndex": page_index,
                "pageSize": page_size
            }
            
            response = await self.client.post(url, json=payload, headers=self.base_headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                logger.error(f"Score API 返回错误: {data.get('error')}")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"抓取游戏评分失败 (game_id={game_id}): {str(e)}")
            raise
    
    def parse_rank_game_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析rank API返回的单个游戏项
        
        Args:
            item: rank API返回的listElements中的单个项
            
        Returns:
            解析后的游戏数据
        """
        game_info = item.get("gameInfo", {})
        comment_info = item.get("commentInfo", {})
        game_card_tags = item.get("gameCardTags", [])
        
        parsed = {
            "external_id": game_info.get("id"),
            "title": game_info.get("title"),
            "title_english": game_info.get("titleInEnglish"),
            "developer_name": game_info.get("developerName"),
            "publisher_name": game_info.get("publisherName"),
            "description_html": game_info.get("detailInHtml"),
            "description": self._extract_text_from_html(game_info.get("detailInHtml", "")),
            "cover_image_url": game_info.get("coverImageUrl"),
            "horizontal_image_url": game_info.get("horizontalImageUrl"),
            "platforms": game_info.get("devicePlatformNames", []),
            "platform_ids": game_info.get("devicePlatformIds", []),
            "tags": [tag.get("caption") for tag in game_info.get("tags", []) if tag.get("caption")],
            "be_official_chinese_enable": game_info.get("beOfficialChineseEnable"),
            "device_requirement_html": game_info.get("deviceRequirementInHtml"),
            "is_published": game_info.get("isPublished"),
            "play_hours_caption": game_info.get("playHoursCaption"),
            "theme_color": game_info.get("themeColor"),
        }
        
        # 提取评分信息
        score_info = game_info.get("scoreInfo", {})
        if score_info:
            parsed["user_score"] = score_info.get("userScore")
            parsed["score_users_count"] = score_info.get("scoreUsersCount")
            parsed["playeds_count"] = score_info.get("playedsCount")
            parsed["want_plays_count"] = score_info.get("wantPlaysCount")
        
        # 提取价格信息（从gameCardTags）
        for tag in game_card_tags:
            if tag.get("showType") == "priceInfo":
                price_info = tag.get("priceInfo", {})
                if price_info:
                    if "is_free" not in parsed:
                        parsed["is_free"] = price_info.get("beFree", False)
                    if "price" not in parsed:
                        parsed["price"] = price_info.get("price")
                    if "price_lowest" not in parsed:
                        parsed["price_lowest"] = price_info.get("priceLowest")
                    if "price_original" not in parsed:
                        parsed["price_original"] = price_info.get("priceOriginal")
                    if "sale_price_rate" not in parsed:
                        parsed["sale_price_rate"] = price_info.get("salePriceRate")
            elif tag.get("showType") == "hotValue":
                parsed["hot_value"] = tag.get("showContent")
        
        # 提取价格信息（从gameInfo.priceInfes）
        price_infes = game_info.get("priceInfes", [])
        if price_infes:
            parsed["price_infes"] = price_infes
        
        # 提取发布时间
        publish_times = game_info.get("publishTimes", [])
        if publish_times:
            for pt in publish_times:
                if pt.get("isPublished"):
                    parsed["publish_date"] = self._parse_date(pt.get("publishTime"))
                    break
        
        # 提取评论信息（第一条评论）
        if comment_info:
            parsed["top_comment"] = {
                "content_html": comment_info.get("contentInHtml"),
                "content": self._extract_text_from_html(comment_info.get("contentInHtml", ""))
            }
        
        # 保存原始数据
        parsed["raw_rank_data"] = item
        
        return parsed
    
    def parse_page_game_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析page API返回的游戏详情
        
        Args:
            data: page API返回的数据
            
        Returns:
            解析后的游戏数据
        """
        game = data.get("game", {})
        if not game:
            return {}
        
        parsed = {
            "external_id": game.get("id"),
            "title": game.get("title"),
            "title_english": game.get("titleInEnglish"),
            "developer_name": game.get("developerName"),
            "publisher_name": game.get("publisherName"),
            "description_html": game.get("detailInHtml"),
            "description": self._extract_text_from_html(game.get("detailInHtml", "")),
            "cover_image_url": game.get("coverImageUrl"),
            "horizontal_image_url": game.get("horizontalImageUrl"),
            "platforms": game.get("devicePlatformNames", []),
            "platform_ids": game.get("devicePlatformIds", []),
            "tags": [tag.get("caption") for tag in game.get("tags", []) if tag.get("caption")],
            "be_official_chinese_enable": game.get("beOfficialChineseEnable"),
            "device_requirement_html": game.get("deviceRequirementInHtml"),
            "is_published": game.get("isPublished"),
            "play_hours_caption": game.get("playHoursCaption"),
        }
        
        # 提取价格信息
        price_infes = game.get("priceInfes", [])
        if price_infes:
            parsed["price_infes"] = price_infes
        
        # 提取发布时间
        publish_times = game.get("publishTimes", [])
        if publish_times:
            for pt in publish_times:
                if pt.get("isPublished"):
                    parsed["publish_date"] = self._parse_date(pt.get("publishTime"))
                    break
        
        # 提取媒体评分
        media_infes = game.get("mediaInfes", [])
        if media_infes:
            parsed["media_scores"] = [
                {
                    "media_name": m.get("mediaName"),
                    "score": m.get("score"),
                    "total_score": m.get("totalScore"),
                    "content_url": m.get("contentUrl")
                }
                for m in media_infes
            ]
        
        # 保存原始数据
        parsed["raw_page_data"] = game
        
        return parsed
    
    def parse_score_game_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析score API返回的评分和评论
        
        Args:
            data: score API返回的数据
            
        Returns:
            解析后的数据
        """
        parsed = {
            "game_id": data.get("gameId"),
            "game_score_info": data.get("gameScoreInfo", {}),
            "reviews": []
        }
        
        # 提取评分信息
        score_info = data.get("gameScoreInfo", {})
        if score_info:
            parsed["score_info"] = {
                "user_score": score_info.get("userScore"),
                "score_users_count": score_info.get("scoreUsersCount"),
                "playeds_count": score_info.get("playedsCount"),
                "want_plays_count": score_info.get("wantPlaysCount"),
                "real_players_score": score_info.get("realPlayersScore"),
                "real_players_count": score_info.get("realPlayersCount"),
                "score_description": score_info.get("scoreDescription")
            }
        
        # 提取评论列表
        list_elements = data.get("listElements", [])
        for idx, element in enumerate(list_elements, start=1):
            comment_info = element.get("commentInfo", {})
            if comment_info:
                review = {
                    "external_comment_id": comment_info.get("id"),
                    "ordernum": idx,
                    "content_html": comment_info.get("contentInHtml"),
                    "content": self._extract_text_from_html(comment_info.get("contentInHtml", "")),
                    "rating": comment_info.get("contentScore"),
                    "publish_time": comment_info.get("publishTimeCaption"),
                    "praises_count": comment_info.get("praisesCount", 0),
                    "replies_count": comment_info.get("repliesCount", 0),
                    "treads_count": comment_info.get("treadsCount", 0),
                    "game_label_platform_names": comment_info.get("gameLabelPlatformNames", []),
                    "content_user_label_type_names": comment_info.get("contentUserLabelTypeNames", []),
                    "author_user_id": element.get("authorUserId"),
                    "author_name": element.get("authorName"),
                    "author_head_image_url": element.get("authorHeadImageUrl"),
                    "raw_data": comment_info
                }
                parsed["reviews"].append(review)
        
        return parsed
    
    def merge_game_data(self, rank_data: Dict[str, Any], page_data: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多个API的数据
        
        Args:
            rank_data: rank API解析后的数据
            page_data: page API解析后的数据
            score_data: score API解析后的数据
            
        Returns:
            合并后的游戏数据
        """
        merged = rank_data.copy() if rank_data else {}
        
        # 优先使用page API的数据
        if page_data:
            for key in ["title", "title_english", "developer_name", "publisher_name", 
                       "description", "description_html", "cover_image_url", "horizontal_image_url",
                       "platforms", "platform_ids", "tags", "be_official_chinese_enable",
                       "device_requirement_html", "is_published", "play_hours_caption"]:
                if key in page_data and page_data[key] is not None:
                    merged[key] = page_data[key]
            
            if "price_infes" in page_data:
                merged["price_infes"] = page_data["price_infes"]
            
            if "media_scores" in page_data:
                merged["media_scores"] = page_data["media_scores"]
        
        # 评分信息合并
        if score_data and "score_info" in score_data:
            score_info = score_data["score_info"]
            for key in ["user_score", "score_users_count", "playeds_count", "want_plays_count",
                       "real_players_score", "real_players_count"]:
                if key in score_info and score_info[key] is not None:
                    merged[key] = score_info[key]
        
        # 评论数据
        if score_data and "reviews" in score_data:
            merged["reviews"] = score_data["reviews"]
        
        # 保存原始数据
        merged["raw_data"] = {
            "rank": rank_data.get("raw_rank_data") if rank_data else None,
            "page": page_data.get("raw_page_data") if page_data else None,
            "score": score_data if score_data else None
        }
        
        return merged
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
