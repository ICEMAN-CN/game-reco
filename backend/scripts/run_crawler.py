# -*- coding: utf-8 -*-
"""
运行游戏数据抓取
支持新的三API抓取流程
"""
import asyncio
import argparse
import sys
import logging
from pathlib import Path
from typing import List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志：完全禁用 SQLAlchemy 的日志输出
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.orm").setLevel(logging.ERROR)
# 禁用所有 SQLAlchemy 相关的日志
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)

from app.database import SessionLocal
from app.services.crawler_service import CrawlerService


def parse_rank_ids(rank_str: str) -> List[int]:
    """解析rankId列表，支持范围如 1-100 或逗号分隔如 1,2,3"""
    rank_ids = []
    for part in rank_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            rank_ids.extend(range(int(start), int(end) + 1))
        else:
            rank_ids.append(int(part))
    return sorted(set(rank_ids))


async def main():
    parser = argparse.ArgumentParser(description="游戏数据抓取工具")
    parser.add_argument("--all", action="store_true", help="抓取所有数据（旧API）")
    parser.add_argument("--offset", type=int, default=0, help="偏移量（旧API）")
    
    # 新API参数
    parser.add_argument("--ranks", type=str, default="1-100", help="要抓取的rankId列表，格式: 1-100 或 1,2,3")
    parser.add_argument("--from-json", action="store_true", help="从JSON文件读取并写入数据库")
    parser.add_argument("--fetch-details", action="store_true", help="对已抓取的rank数据，调用page和score API获取详情")
    parser.add_argument("--reviews-only", action="store_true", help="从games表读取所有游戏，重新抓取并保存所有reviews")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数（用于--reviews-only），默认5")
    parser.add_argument("--delay", type=float, default=2.0, help="批次延迟（秒，用于--reviews-only），默认2.0")
    parser.add_argument("--limit", type=int, help="限制处理的游戏数量（用于--reviews-only测试或旧API）")
    
    args = parser.parse_args()
    
    service = CrawlerService()
    
    try:
        # reviews-only 流程（优先处理）
        if args.reviews_only:
            print("=" * 60)
            print("开始重新抓取所有 reviews...")
            print("=" * 60)
            
            db = SessionLocal()
            try:
                stats = await service.crawl_all_reviews(
                    db,
                    concurrency=args.concurrency,
                    delay=args.delay,
                    limit=args.limit
                )
                
                print(f"\n{'='*60}")
                print(f"✓ Reviews 抓取完成！")
                print(f"  总游戏数: {stats['total_games']}")
                print(f"  成功: {stats['success_count']} 个")
                print(f"  失败: {stats['failed_count']} 个")
                print(f"  保存评论总数: {stats['total_reviews']} 条")
                print(f"{'='*60}\n")
            finally:
                db.close()
                await service.crawler.close()
            return
        
        # 新API流程
        if args.from_json:
            print("从JSON文件读取数据并写入数据库...")
            rank_ids = parse_rank_ids(args.ranks)
            games_data = service.load_and_parse_json_files(rank_ids)
            print(f"从JSON加载了 {len(games_data)} 个游戏")
            
            db = SessionLocal()
            try:
                if args.fetch_details:
                    print("获取游戏详情（page和score API）...")
                    print(f"使用并行处理，并发数: 5，批次延迟: 2秒")
                    print(f"抓一批写一批模式，实时显示写入统计\n")
                    
                    # 检查表是否存在，只在开始时输出一次
                    from sqlalchemy import inspect
                    inspector = inspect(db.bind)
                    # 明确指定检查 public schema
                    tables = set(inspector.get_table_names(schema='public'))
                    missing_tables = []
                    required_tables = {
                        "game_rank_relations": "005_create_game_relations_tables.sql",
                        "game_prices": "005_create_game_relations_tables.sql",
                        "game_media_scores": "005_create_game_relations_tables.sql",
                        "reviews": "006_create_reviews_table.sql",
                    }
                    for table, sql_file in required_tables.items():
                        if table not in tables:
                            missing_tables.append((table, sql_file))
                    
                    if missing_tables:
                        print(f"⚠️  以下表不存在，将跳过相关数据保存：")
                        sql_files = {}
                        for table, sql_file in missing_tables:
                            if sql_file not in sql_files:
                                sql_files[sql_file] = []
                            sql_files[sql_file].append(table)
                        
                        for sql_file, table_list in sql_files.items():
                            print(f"  - {', '.join(table_list)} (需要执行: database/init/{sql_file})")
                        print(f"\n💡 提示: 运行 'python3 scripts/check_tables.py' 检查所有表状态\n")
                    
                    # 累计统计
                    total_stats = {
                        "saved_count": 0,
                        "updated_count": 0,
                        "failed_count": 0,
                        "relations_stats": {
                            "rank_relations": 0,
                            "prices": 0,
                            "media_scores": 0,
                            "reviews": 0
                        }
                    }
                    
                    async def on_batch_complete(batch_games, batch_start, batch_end):
                        """批次完成回调：写入数据库并显示统计"""
                        batch_stats = service.save_games_to_db(db, batch_games, show_progress=False)
                        
                        # 累加统计
                        total_stats["saved_count"] += batch_stats["saved_count"]
                        total_stats["updated_count"] += batch_stats["updated_count"]
                        total_stats["failed_count"] += batch_stats["failed_count"]
                        for key in total_stats["relations_stats"]:
                            total_stats["relations_stats"][key] += batch_stats["relations_stats"][key]
                        
                        # 显示批次统计（简洁格式）
                        print(f"[批次 {batch_start + 1}-{batch_end}] ✓ 写入完成 | "
                              f"游戏: +{batch_stats['saved_count']} ↑{batch_stats['updated_count']} ✗{batch_stats['failed_count']} | "
                              f"关联: 榜单{batch_stats['relations_stats']['rank_relations']} "
                              f"价格{batch_stats['relations_stats']['prices']} "
                              f"评分{batch_stats['relations_stats']['media_scores']} "
                              f"评论{batch_stats['relations_stats']['reviews']} | "
                              f"累计: 游戏{total_stats['saved_count'] + total_stats['updated_count']} "
                              f"关联{sum(total_stats['relations_stats'].values())}")
                    
                    await service.fetch_game_details_batch(
                        games_data, 
                        concurrency=5, 
                        delay_between_batches=2.0,
                        on_batch_complete=on_batch_complete
                    )
                    
                    # 显示最终统计
                    print(f"\n{'='*60}")
                    print(f"✓ 全部完成！最终统计:")
                    print(f"  游戏: 新增 {total_stats['saved_count']}, 更新 {total_stats['updated_count']}, 失败 {total_stats['failed_count']}")
                    print(f"  关联数据:")
                    print(f"    - 榜单关联: {total_stats['relations_stats']['rank_relations']}")
                    print(f"    - 价格信息: {total_stats['relations_stats']['prices']}")
                    print(f"    - 媒体评分: {total_stats['relations_stats']['media_scores']}")
                    print(f"    - 评论: {total_stats['relations_stats']['reviews']}")
                    print(f"{'='*60}\n")
                else:
                    # 不获取详情，直接写入
                    stats = service.save_games_to_db(db, games_data)
                    print(f"✓ 完成！共保存 {stats['saved_count']} 条游戏数据")
            finally:
                db.close()
        
        elif args.fetch_details:
            print("仅获取游戏详情（需要先有JSON文件）...")
            rank_ids = parse_rank_ids(args.ranks)
            games_data = service.load_and_parse_json_files(rank_ids)
            
            print(f"获取 {len(games_data)} 个游戏的详情...")
            print(f"使用并行处理，并发数: 5，批次延迟: 2秒")
            await service.fetch_game_details_batch(
                games_data, 
                concurrency=5, 
                delay_between_batches=2.0
            )
            
            # 保存更新后的数据到JSON
            for rank_id in rank_ids:
                # 这里可以重新组织数据保存，暂时跳过
                pass
            
            print("✓ 完成！")
        
        else:
            # 抓取榜单数据到JSON
            rank_ids = parse_rank_ids(args.ranks)
            print(f"准备抓取榜单数据 (共 {len(rank_ids)} 个榜单)...")
            results = await service.crawl_all_ranks(rank_ids)
            
            print(f"\n数据已保存到 backend/data/rank_*.json")
            print(f"下一步: 使用 --from-json 参数将数据写入数据库")
        
        # 旧API流程（保持兼容）
        if args.all or args.limit:
            db = SessionLocal()
            try:
                if args.all:
                    print("开始抓取所有游戏数据（旧API）...")
                    total = await service.crawl_all(db)
                    print(f"✓ 完成！共保存 {total} 条游戏数据")
                elif args.limit:
                    print(f"开始抓取 {args.limit} 条游戏数据（旧API）...")
                    saved = await service.crawl_and_save(db, limit=args.limit, offset=args.offset)
                    print(f"✓ 完成！共保存 {saved} 条游戏数据")
            finally:
                db.close()
                await service.crawler.close()
        
        if not any([args.from_json, args.fetch_details, args.all, args.limit, args.reviews_only]):
            print("请指定操作参数")
            parser.print_help()
            
    except Exception as e:
        print(f"❌ 抓取失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await service.crawler.close()


if __name__ == "__main__":
    asyncio.run(main())

