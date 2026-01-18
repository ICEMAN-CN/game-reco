"""
RAG 服务
"""
import logging
import re
import json
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.game import Game
from app.services.embedding_service import EmbeddingService
from app.model_providers import LocalModelProvider, OpenAIProvider, AnthropicProvider
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        
        # 创建聊天模型提供者
        provider_type = settings.chat_model_provider
        if provider_type == "local":
            self.chat_provider = LocalModelProvider(
                model_name=settings.chat_model_name,
                base_url=settings.chat_base_url,
                api_key=settings.chat_api_key
            )
        elif provider_type == "openai":
            self.chat_provider = OpenAIProvider(
                model_name=settings.chat_model_name,
                base_url=settings.chat_base_url,
                api_key=settings.chat_api_key
            )
        elif provider_type == "anthropic":
            self.chat_provider = AnthropicProvider(
                model_name=settings.chat_model_name,
                base_url=settings.chat_base_url,
                api_key=settings.chat_api_key
            )
        else:
            raise ValueError(f"不支持的聊天模型提供者: {provider_type}")
    
    async def search_similar_games(
        self,
        db: Session,
        query: str,
        limit: int = 5
    ) -> List[Game]:
        """搜索相似游戏 (使用向量检索)"""
        from app.models.game_embedding import GameEmbedding
        
        logger.info("=" * 50)
        logger.info("[RAG] Step 1: 生成查询 Embedding")
        logger.info(f"[RAG] 查询文本: {query[:100]}...")
        
        # 生成查询 embedding
        query_embeddings = await self.embedding_service.provider.embed_texts([query])
        if not query_embeddings or not query_embeddings[0]:
            # 如果 embedding 失败，降级到文本搜索
            logger.warning("[RAG] Embedding 生成失败，降级到文本搜索")
            games = db.query(Game).filter(
                Game.description.ilike(f"%{query}%")
            ).limit(limit).all()
            return games
        
        query_embedding = query_embeddings[0]
        logger.info(f"[RAG] 生成 Embedding 成功，维度: {len(query_embedding)}")
        
        # 向量检索 (使用 pgvector)
        try:
            from app.models.game_embedding import GameEmbedding, VECTOR_AVAILABLE
            
            if not VECTOR_AVAILABLE:
                raise ImportError("pgvector 未安装")
            
            # 检查是否有 embedding 数据
            embedding_count = db.query(GameEmbedding).count()
            logger.info(f"[RAG] Step 2: 向量检索 (数据库中有 {embedding_count} 条 embedding)")
            
            if embedding_count == 0:
                logger.warning("[RAG] 没有找到 embedding 数据，降级到文本搜索")
                games = db.query(Game).filter(
                    Game.description.ilike(f"%{query}%")
                ).limit(limit).all()
                return games
            
            # 使用原生 SQL 查询进行向量相似度搜索
            # <=> 是 pgvector 的余弦距离操作符
            query_vec_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            logger.info("[RAG] 执行向量相似度查询...")
            result = db.execute(
                text("""
                    SELECT game_id, 
                        1 - (embedding_vector <=> CAST(:query_vec AS vector)) as similarity
                    FROM game_embeddings
                    ORDER BY embedding_vector <=> CAST(:query_vec AS vector)
                    LIMIT :limit
                """),
                {
                    "query_vec": query_vec_str,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            if rows:
                logger.info(f"[RAG] Step 3: 检索结果 (找到 {len(rows)} 个相似游戏)")
                for i, row in enumerate(rows):
                    logger.info(f"  [{i+1}] game_id={row[0]}, 相似度={row[1]:.4f}")
                
                game_ids = [row[0] for row in rows]
                games = db.query(Game).filter(Game.id.in_(game_ids)).all()
                # 保持顺序
                game_dict = {g.id: g for g in games}
                ordered_games = [game_dict[gid] for gid in game_ids if gid in game_dict]
                
                logger.info("[RAG] 检索到的游戏:")
                for i, game in enumerate(ordered_games):
                    logger.info(f"  [{i+1}] {game.title}")
                logger.info("=" * 50)
                
                return ordered_games
            else:
                # 如果没有结果，降级到文本搜索
                logger.warning("[RAG] 向量检索无结果，降级到文本搜索")
                games = db.query(Game).filter(
                    Game.description.ilike(f"%{query}%")
                ).limit(limit).all()
                return games
        except Exception as e:
            # 如果向量检索失败，降级到文本搜索
            logger.warning(f"[RAG] 向量检索失败: {str(e)}，降级到文本搜索")
            games = db.query(Game).filter(
                Game.description.ilike(f"%{query}%")
            ).limit(limit).all()
            return games
    
    async def generate_recommendation(
        self,
        db: Session,
        user_query: str,
        context_games: Optional[List[Game]] = None
    ) -> str:
        """生成游戏推荐"""
        logger.info("[RAG] Step 4: 生成推荐回复")
        
        # 如果没有提供上下文游戏，先搜索相似游戏
        if not context_games:
            context_games = await self.search_similar_games(db, user_query, limit=5)
        
        # 构建上下文 - 提供更详细的游戏信息
        games_to_recommend = context_games[:3]  # 只推荐前3个
        context = "【可推荐的游戏列表】\n"
        for i, game in enumerate(games_to_recommend, 1):
            context += f"\n{i}. **{game.title}**"
            if game.title_english:
                context += f" ({game.title_english})"
            context += "\n"
            if game.description:
                context += f"   简介: {game.description[:300]}...\n"
            if game.tags:
                context += f"   标签: {', '.join(game.tags[:8])}\n"
            if game.platforms:
                context += f"   平台: {', '.join(game.platforms)}\n"
            if game.user_score:
                context += f"   评分: {game.user_score}\n"
        
        logger.info(f"[RAG] 构建上下文，包含 {len(games_to_recommend)} 个游戏")
        logger.info(f"[RAG] 上下文长度: {len(context)} 字符")
        
        # 构建提示 - 强制 LLM 只从列表中推荐
        system_prompt = """你是一个专业的游戏推荐助手。

【重要规则】
1. 你只能从「可推荐的游戏列表」中选择游戏进行推荐
2. 不要推荐列表之外的任何游戏
3. 即使你知道其他更合适的游戏，也只能从列表中选择
4. 为每个推荐的游戏说明推荐理由，解释为什么它符合用户需求
5. 用自然流畅的语言回复，不要使用编号列表格式"""

        user_prompt = f"""{context}

【用户需求】
{user_query}

请从上面的游戏列表中，为用户推荐最合适的游戏，并详细说明每个游戏的推荐理由。记住：只能推荐列表中的游戏！"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info("[RAG] Step 5: 调用 LLM 生成回复...")
        
        # 生成回复
        response = await self.chat_provider.chat(messages, stream=False)
        result = response if isinstance(response, str) else ""
        
        logger.info(f"[RAG] 生成完成，回复长度: {len(result)} 字符")
        logger.info("=" * 50)
        
        return result
    
    async def generate_recommendation_with_selection(
        self,
        db: Session,
        user_query: str,
        context_games: List[Game]
    ) -> Dict[str, Any]:
        """
        生成游戏推荐（带智能选择）
        
        - 从候选游戏中选择最合适的 3 个
        - 排除用户问题中提到的游戏
        - 生成后续推荐问题
        
        返回: {
            'response': str,  # 推荐文字
            'recommended_game_ids': List[int],  # 推荐的游戏 ID
            'suggested_questions': List[str]  # 后续推荐问题
        }
        """
        logger.info("[RAG] Step 4: 生成推荐回复（带智能选择）")
        
        # 构建游戏列表上下文
        context = "【候选游戏列表】\n"
        for i, game in enumerate(context_games, 1):
            context += f"\n[ID:{game.id}] {game.title}"
            if game.title_english:
                context += f" ({game.title_english})"
            context += "\n"
            if game.description:
                context += f"   简介: {game.description[:250]}...\n"
            if game.tags:
                context += f"   标签: {', '.join(game.tags[:6])}\n"
            if game.platforms:
                context += f"   平台: {', '.join(game.platforms)}\n"
            if game.user_score:
                context += f"   评分: {game.user_score}\n"
        
        logger.info(f"[RAG] 构建上下文，包含 {len(context_games)} 个候选游戏")
        
        # 构建提示 - 让 LLM 选择并排除用户提到的游戏
        system_prompt = """你是一个专业的游戏推荐助手。

【核心规则】
1. 从「候选游戏列表」中选择最符合用户需求的 3 款游戏进行推荐
2. **重要**：如果用户在问题中提到了某款游戏（如"类似XXX的游戏"），则不要推荐那款游戏本身，要推荐其他类似的游戏
3. 只能推荐列表中的游戏，不能推荐列表之外的游戏
4. 用自然流畅的语言介绍每款推荐的游戏，说明推荐理由

【输出格式】
请按以下格式输出：

---推荐内容开始---
（在这里写你的推荐文字，自然地介绍 3 款游戏及推荐理由）
---推荐内容结束---

---游戏ID---
ID1,ID2,ID3
---游戏ID结束---

---后续问题---
问题1
问题2
问题3
---后续问题结束---

注意：
- 游戏ID 必须是候选列表中的 [ID:数字] 格式里的数字
- 后续问题要与用户兴趣相关，引导用户探索更多游戏"""

        user_prompt = f"""{context}

【用户需求】
{user_query}

请根据用户需求，从候选列表中选择 3 款最合适的游戏进行推荐。
记住：如果用户提到了"类似XX游戏"，不要推荐XX本身！"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info("[RAG] Step 5: 调用 LLM 生成回复...")
        
        # 生成回复
        raw_response = await self.chat_provider.chat(messages, stream=False)
        raw_response = raw_response if isinstance(raw_response, str) else ""
        
        logger.info(f"[RAG] LLM 原始回复长度: {len(raw_response)} 字符")
        
        # 解析响应（传入用户查询用于排除用户提到的游戏）
        result = self._parse_recommendation_response(raw_response, context_games, user_query)
        
        logger.info(f"[RAG] 解析完成，推荐游戏 IDs: {result['recommended_game_ids']}")
        logger.info(f"[RAG] 后续问题: {result['suggested_questions']}")
        logger.info("=" * 50)
        
        return result
    
    def _parse_recommendation_response(
        self,
        raw_response: str,
        context_games: List[Game],
        user_query: str = ""
    ) -> Dict[str, Any]:
        """解析 LLM 的推荐响应"""
        
        result = {
            'response': '',
            'recommended_game_ids': [],
            'suggested_questions': []
        }
        
        # 尝试解析推荐内容
        content_match = re.search(
            r'---推荐内容开始---\s*(.*?)\s*---推荐内容结束---',
            raw_response,
            re.DOTALL
        )
        if content_match:
            response_text = content_match.group(1).strip()
        else:
            # 如果没有找到格式标记，使用整个响应（去掉可能的元数据部分）
            # 尝试去掉 ---游戏ID--- 和 ---后续问题--- 部分
            response_text = re.sub(r'---游戏ID---.*?---游戏ID结束---', '', raw_response, flags=re.DOTALL)
            response_text = re.sub(r'---后续问题---.*?---后续问题结束---', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()
        
        # 清除回复中的 ID 标记（如 "**ID:76**"、"[ID:76]"、"ID:76" 等）
        response_text = re.sub(r'\*?\*?\[?ID:\d+\]?\*?\*?\s*', '', response_text)
        # 清除可能残留的格式标记
        response_text = re.sub(r'---[^-]+---', '', response_text)
        result['response'] = response_text.strip()
        
        # 尝试解析游戏 ID
        id_match = re.search(
            r'---游戏ID---\s*(.*?)\s*---游戏ID结束---',
            raw_response,
            re.DOTALL
        )
        if id_match:
            id_str = id_match.group(1).strip()
            # 提取数字
            ids = re.findall(r'\d+', id_str)
            # 验证 ID 是否在候选游戏中，并排除用户提到的游戏
            valid_game_ids = {game.id for game in context_games}
            excluded_titles = self._extract_game_titles_from_query(user_query)
            
            for id_str in ids[:6]:  # 检查更多 ID 以防前面的被排除
                game_id = int(id_str)
                if game_id in valid_game_ids:
                    # 检查这个游戏是否被用户提到
                    game = next((g for g in context_games if g.id == game_id), None)
                    if game and game.title not in excluded_titles:
                        result['recommended_game_ids'].append(game_id)
                        if len(result['recommended_game_ids']) >= 3:
                            break
        
        # 如果没有解析到足够的 ID，尝试从响应文字中提取提到的游戏
        if len(result['recommended_game_ids']) < 3:
            excluded_titles = self._extract_game_titles_from_query(user_query)
            for game in context_games:
                if game.id not in result['recommended_game_ids']:
                    if game.title in result['response'] and game.title not in excluded_titles:
                        result['recommended_game_ids'].append(game.id)
                        logger.info(f"[RAG] 从文字匹配到游戏: {game.title} (ID: {game.id})")
                        if len(result['recommended_game_ids']) >= 3:
                            break
        
        # 尝试解析后续问题
        questions_match = re.search(
            r'---后续问题---\s*(.*?)\s*---后续问题结束---',
            raw_response,
            re.DOTALL
        )
        if questions_match:
            questions_str = questions_match.group(1).strip()
            # 按行分割
            questions = [q.strip() for q in questions_str.split('\n') if q.strip()]
            # 去掉可能的序号
            questions = [re.sub(r'^[\d\.\)]+\s*', '', q) for q in questions]
            result['suggested_questions'] = questions[:3]
        
        # 如果没有解析到后续问题，生成默认问题
        if not result['suggested_questions']:
            result['suggested_questions'] = self._generate_default_questions(context_games)
        
        return result
    
    def _extract_game_titles_from_query(self, user_query: str) -> set:
        """
        从用户查询中提取可能提到的游戏名称
        
        例如：
        - "类似对马岛之魂的游戏" -> {"对马岛之魂"}
        - "像巫师3一样的RPG" -> {"巫师3"}
        """
        excluded = set()
        
        # 常见的游戏名称模式
        # 1. 《游戏名》格式
        matches = re.findall(r'《([^》]+)》', user_query)
        excluded.update(matches)
        
        # 2. "类似XXX" / "像XXX" 模式
        patterns = [
            r'类似[「『]?([^」』\s,，。、]+)[」』]?',
            r'像[「『]?([^」』\s,，。、]+)[」』]?(?:一样|这样)?',
            r'和[「『]?([^」』\s,，。、]+)[」』]?(?:类似|相似)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, user_query)
            excluded.update(matches)
        
        # 3. 常见游戏名变体
        game_aliases = {
            "对马岛之魂": ["对马岛", "Ghost of Tsushima", "对马"],
            "巫师3": ["巫师3：狂猎", "The Witcher 3", "狂猎"],
            "原神": ["Genshin Impact", "genshin"],
            "艾尔登法环": ["Elden Ring", "老头环", "法环"],
            "塞尔达": ["塞尔达传说", "Zelda", "王国之泪", "旷野之息"],
        }
        
        query_lower = user_query.lower()
        for main_name, aliases in game_aliases.items():
            if main_name in user_query:
                excluded.add(main_name)
            for alias in aliases:
                if alias.lower() in query_lower:
                    excluded.add(main_name)
        
        logger.info(f"[RAG] 从用户查询中提取的排除游戏: {excluded}")
        return excluded
    
    def _generate_default_questions(self, context_games: List[Game]) -> List[str]:
        """生成默认的后续问题"""
        questions = []
        
        # 基于游戏标签生成问题
        all_tags = []
        for game in context_games[:5]:
            if game.tags:
                all_tags.extend(game.tags[:3])
        
        unique_tags = list(set(all_tags))[:3]
        
        if unique_tags:
            questions.append(f"有没有更多{unique_tags[0]}类型的游戏推荐？")
        
        if len(unique_tags) > 1:
            questions.append(f"想找一款{unique_tags[1]}风格的游戏")
        
        # 添加一个通用问题
        questions.append("有什么适合周末放松玩的游戏吗？")
        
        return questions[:3]