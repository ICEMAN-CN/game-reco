# -*- coding: utf-8 -*-
"""
批量生成游戏 Embedding（包含价格、评论、媒体评分）
支持逐个调用API避免OOM
"""
import asyncio
import json
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.game import Game
from app.models.game_embedding import GameEmbedding
from app.services.embedding_service import EmbeddingService
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def batch_embed_games(limit: int = None, batch_size: int = 10, skip_existing: bool = True):
    """
    批量生成游戏 embedding
    
    Args:
        limit: 限制处理的游戏数量
        batch_size: 每批提交事务的游戏数量（不是API调用批次）
        skip_existing: 是否跳过已有embedding的游戏
    """
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    try:
        # 获取所有游戏
        query = db.query(Game)
        
        # 获取已生成 embedding 的游戏ID
        if skip_existing:
            existing_game_ids = set(
                db.query(GameEmbedding.game_id).distinct().all()
            )
            existing_game_ids = {gid[0] for gid in existing_game_ids}
            
            # 过滤掉已处理的游戏
            if existing_game_ids:
                query = query.filter(~Game.id.in_(existing_game_ids))
        
        if limit:
            query = query.limit(limit)
        
        games = query.all()
        total = len(games)
        
        if total == 0:
            print("没有需要处理的游戏")
            return
        
        print(f"开始处理 {total} 个游戏的 embedding...")
        print(f"事务批次大小: {batch_size}")
        print(f"跳过已有: {skip_existing}")
        print("=" * 60)
        
        processed = 0
        failed = 0
        
        # 逐个处理游戏（避免OOM），但按批次提交事务
        for idx, game in enumerate(games, 1):
            try:
                # 生成 embedding（包含价格、评论、媒体评分）
                logger.info(f"[{idx}/{total}] 开始处理游戏 {game.id} ({game.title[:30]})")
                
                embedding_vector, chunk_text = await embedding_service.embed_game(game, db)
                
                # 详细日志：检查 embedding_vector 的结构
                logger.debug(f"  embedding_vector type: {type(embedding_vector)}")
                logger.debug(f"  embedding_vector length: {len(embedding_vector) if embedding_vector else 'None'}")
                if embedding_vector and len(embedding_vector) > 0:
                    logger.debug(f"  first element type: {type(embedding_vector[0])}")
                    logger.debug(f"  first 5 elements: {embedding_vector[:5]}")
                    logger.debug(f"  last 5 elements: {embedding_vector[-5:]}")
                
                if not embedding_vector or len(embedding_vector) == 0:
                    print(f"  [{idx}/{total}] ⚠️  游戏 {game.id} ({game.title[:30]}) embedding 为空，跳过")
                    failed += 1
                    continue
                
                # 验证向量维度
                if len(embedding_vector) != 2560:
                    logger.error(
                        f"  [{idx}/{total}] 向量维度错误: {len(embedding_vector)} (期望: 2560)\n"
                        f"  chunk_text 长度: {len(chunk_text) if chunk_text else 'None'}\n"
                        f"  chunk_text 前200字符: {chunk_text[:200] if chunk_text else 'None'}"
                    )
                    print(f"  [{idx}/{total}] ⚠️  游戏 {game.id} 向量维度错误: {len(embedding_vector)} (期望: 2560)")
                    failed += 1
                    continue
                
                # 转换 embedding 为字符串格式 (pgvector 需要)
                embedding_str = "[" + ",".join(map(str, embedding_vector)) + "]"
                
                # 准备 metadata JSON 字符串（修复：dict 需要转换为 JSON 字符串）
                metadata_dict = {
                    "game_id": game.id,
                    "external_id": game.external_id,
                    "title": game.title
                }
                metadata_json_str = json.dumps(metadata_dict, ensure_ascii=False)
                
                # 检查是否已存在
                existing = db.query(GameEmbedding).filter(
                    GameEmbedding.game_id == game.id
                ).first()
                
                if existing:
                    # 更新
                    db.execute(
                        text("""
                            UPDATE game_embeddings 
                            SET embedding_vector = CAST(:vec AS vector),
                                chunk_text = :text,
                                model_name = :model,
                                metadata_json = CAST(:metadata AS jsonb)
                            WHERE game_id = :game_id
                        """),
                        {
                            "vec": embedding_str,
                            "text": chunk_text,
                            "model": embedding_service.provider.model_name,
                            "metadata": metadata_json_str,
                            "game_id": game.id
                        }
                    )
                    print(f"  [{idx}/{total}] ✓ 更新 {game.id} ({game.title[:30]})")
                else:
                    # 插入
                    db.execute(
                        text("""
                            INSERT INTO game_embeddings 
                            (game_id, embedding_vector, chunk_text, model_name, metadata_json)
                            VALUES (:game_id, CAST(:vec AS vector), :text, :model, CAST(:metadata AS jsonb))
                        """),
                        {
                            "game_id": game.id,
                            "vec": embedding_str,
                            "text": chunk_text,
                            "model": embedding_service.provider.model_name,
                            "metadata": metadata_json_str
                        }
                    )
                    print(f"  [{idx}/{total}] ✓ 创建 {game.id} ({game.title[:30]})")
                
                processed += 1
                
                # 每处理 batch_size 个游戏提交一次事务
                if processed % batch_size == 0:
                    try:
                        db.commit()
                        print(f"  → 已提交 {processed} 个游戏")
                    except Exception as e:
                        logger.error(f"  提交失败: {str(e)}")
                        print(f"  ❌ 提交失败: {str(e)}")
                        db.rollback()
                        # 提交失败不影响继续处理，但需要减少成功计数
                        processed -= batch_size
                        failed += batch_size
                
            except Exception as e:
                logger.exception(f"  [{idx}/{total}] 处理失败: {game.id} ({game.title[:30] if game.title else 'N/A'})")
                print(f"  [{idx}/{total}] ❌ {game.id} ({game.title[:30] if game.title else 'N/A'}) 失败: {str(e)}")
                failed += 1
                # 单个游戏失败后 rollback，确保后续操作在干净的事务中
                try:
                    db.rollback()
                except:
                    pass
                continue
        
        # 提交剩余的游戏（如果有）
        if processed > 0 and processed % batch_size != 0:
            try:
                db.commit()
                print(f"  → 已提交剩余 {processed % batch_size} 个游戏")
            except Exception as e:
                logger.error(f"  最终提交失败: {str(e)}")
                print(f"  ❌ 最终提交失败: {str(e)}")
                db.rollback()
        
        print(f"\n{'='*60}")
        print(f"处理完成!")
        print(f"  总计: {total} 个游戏")
        print(f"  成功: {processed} 个")
        print(f"  失败: {failed} 个")
        print(f"{'='*60}")
        
    except Exception as e:
        logger.exception(f"批量处理失败")
        print(f"❌ 批量处理失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量生成游戏 Embedding")
    parser.add_argument("--limit", type=int, help="限制处理的游戏数量")
    parser.add_argument("--batch-size", type=int, default=10, help="每批提交事务的游戏数量")
    parser.add_argument("--force", action="store_true", help="强制重新生成已有embedding")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    asyncio.run(batch_embed_games(
        limit=args.limit, 
        batch_size=args.batch_size,
        skip_existing=not args.force
    ))
