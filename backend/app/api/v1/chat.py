"""
AI 聊天推荐 API
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.services.rag_service import RAGService
from app.schemas.game import GameResponse

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = RAGService()


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    games: Optional[List[GameResponse]] = None
    suggested_questions: Optional[List[str]] = None  # 后续推荐问题


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI 聊天推荐 (非流式)"""
    try:
        logger.info(f"[RAG] 收到用户查询: {request.message[:100]}")
        
        # 搜索更多相关游戏（10个），给 LLM 更多选择空间
        logger.info("[RAG] 开始向量检索...")
        context_games = await rag_service.search_similar_games(db, request.message, limit=10)
        logger.info(f"[RAG] 检索到 {len(context_games)} 个相关游戏:")
        for i, game in enumerate(context_games):
            logger.info(f"  [{i+1}] {game.title} (ID: {game.id})")
        
        # 生成推荐（LLM 会从 10 个中选择 3 个，并排除用户提到的游戏）
        logger.info("[RAG] 生成推荐回复...")
        result = await rag_service.generate_recommendation_with_selection(
            db,
            request.message,
            context_games
        )
        logger.info(f"[RAG] 生成完成，回复长度: {len(result['response'])}")
        logger.info(f"[RAG] 推荐游戏 IDs: {result['recommended_game_ids']}")
        
        # 根据 LLM 选择的游戏 ID 获取游戏信息
        recommended_games = []
        for game_id in result['recommended_game_ids']:
            for game in context_games:
                if game.id == game_id:
                    recommended_games.append(game)
                    break
        
        # 如果 LLM 没有返回有效 ID，从响应文字中提取推荐的游戏
        if not recommended_games:
            logger.warning("[RAG] 未能解析游戏 ID，尝试从文字中匹配...")
            response_text = result['response']
            for game in context_games:
                # 检查游戏名是否在推荐文字中被提及
                if game.title in response_text:
                    # 排除用户问题中提到的游戏
                    if game.title not in request.message:
                        recommended_games.append(game)
                        logger.info(f"[RAG] 从文字匹配到游戏: {game.title}")
                        if len(recommended_games) >= 3:
                            break
        
        return ChatResponse(
            response=result['response'],
            games=[GameResponse.model_validate(game) for game in recommended_games[:3]],
            suggested_questions=result.get('suggested_questions', [])
        )
    except Exception as e:
        logger.exception(f"[RAG] 处理失败: {str(e)}")
        error_message = str(e)
        
        # 提供更友好的错误信息
        if "无法连接到 Ollama" in error_message or "All connection attempts failed" in error_message:
            error_message = (
                "无法连接到 AI 模型服务。"
                "请确保 Ollama 服务正在运行。"
                "启动命令: ollama serve"
            )
        elif "无法连接到 Embedding" in error_message:
            error_message = (
                "无法连接到 Embedding 服务。"
                "请确保 Embedding 服务正在运行。"
            )
        
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI 聊天推荐 (流式)"""
    async def generate():
        try:
            logger.info(f"[RAG-Stream] 收到用户查询: {request.message[:100]}")
            
            # 搜索相关游戏
            logger.info("[RAG-Stream] 开始向量检索...")
            context_games = await rag_service.search_similar_games(db, request.message, limit=5)
            logger.info(f"[RAG-Stream] 检索到 {len(context_games)} 个相关游戏:")
            for i, game in enumerate(context_games):
                logger.info(f"  [{i+1}] {game.title} (ID: {game.id})")
            
            # 构建上下文 - 提供更详细的游戏信息
            games_to_recommend = context_games[:3]
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
            
            logger.info(f"[RAG-Stream] 构建上下文完成，长度: {len(context)}")
            
            # 构建消息 - 强制 LLM 只从列表中推荐
            system_prompt = """你是一个专业的游戏推荐助手。

【重要规则】
1. 你只能从「可推荐的游戏列表」中选择游戏进行推荐
2. 不要推荐列表之外的任何游戏
3. 即使你知道其他更合适的游戏，也只能从列表中选择
4. 为每个推荐的游戏说明推荐理由，解释为什么它符合用户需求
5. 用自然流畅的语言回复，不要使用编号列表格式"""

            user_prompt = f"""{context}

【用户需求】
{request.message}

请从上面的游戏列表中，为用户推荐最合适的游戏，并详细说明每个游戏的推荐理由。记住：只能推荐列表中的游戏！"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info("[RAG-Stream] 开始流式生成回复...")
            
            # 流式生成（需要先 await 获取 async generator）
            stream_gen = await rag_service.chat_provider.chat(messages, stream=True)
            async for chunk in stream_gen:
                yield f"data: {chunk}\n\n"
            
            logger.info("[RAG-Stream] 流式生成完成")
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception(f"[RAG-Stream] 处理失败: {str(e)}")
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
