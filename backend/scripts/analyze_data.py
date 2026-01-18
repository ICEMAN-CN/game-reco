# -*- coding: utf-8 -*-
"""
数据库数据校对脚本
检查数据错误和缺失情况
"""
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, text, and_, or_

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.game import Game
from app.models.game_price import GamePrice
from app.models.game_rank_relation import GameRankRelation
from app.models.game_media_score import GameMediaScore
from app.models.review import Review
from app.models.game_embedding import GameEmbedding


def check_data_quality():
    """检查数据质量和完整性"""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("Game Odyssey 数据校对报告")
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        games_count = db.query(func.count(Game.id)).scalar()
        print(f"\n总游戏数: {games_count:,}")
        
        # ========== 1. 基础数据完整性检查 ==========
        print("\n【1. 基础数据完整性检查】")
        print("-" * 80)
        
        # 缺失关键字段的游戏
        missing_title = db.query(func.count(Game.id)).filter(
            or_(Game.title.is_(None), Game.title == "")
        ).scalar()
        missing_external_id = db.query(func.count(Game.id)).filter(
            Game.external_id.is_(None)
        ).scalar()
        missing_description = db.query(func.count(Game.id)).filter(
            or_(Game.description.is_(None), Game.description == "")
        ).scalar()
        missing_platforms = db.query(func.count(Game.id)).filter(
            or_(Game.platforms.is_(None), func.array_length(Game.platforms, 1).is_(None))
        ).scalar()
        
        print(f"缺失标题:           {missing_title:>6,} ({missing_title/games_count*100:.1f}%)")
        print(f"缺失 External ID:   {missing_external_id:>6,} ({missing_external_id/games_count*100:.1f}%)")
        print(f"缺失描述:           {missing_description:>6,} ({missing_description/games_count*100:.1f}%)")
        print(f"缺失平台信息:       {missing_platforms:>6,} ({missing_platforms/games_count*100:.1f}%)")
        
        # ========== 2. 评分数据检查 ==========
        print("\n【2. 评分数据检查】")
        print("-" * 80)
        
        # 有评分的游戏统计
        games_with_score = db.query(func.count(Game.id)).filter(
            Game.user_score.isnot(None)
        ).scalar()
        
        if games_with_score > 0:
            score_stats = db.query(
                func.min(Game.user_score).label('min'),
                func.max(Game.user_score).label('max'),
                func.avg(Game.user_score).label('avg'),
                func.percentile_cont(0.5).within_group(Game.user_score).label('median')
            ).filter(Game.user_score.isnot(None)).first()
            
            print(f"有评分的游戏:       {games_with_score:>6,} ({games_with_score/games_count*100:.1f}%)")
            print(f"评分范围:           {float(score_stats.min):.1f} ~ {float(score_stats.max):.1f}")
            print(f"平均评分:           {float(score_stats.avg):.2f}")
            print(f"中位数评分:         {float(score_stats.median):.2f}")
            
            # 异常评分检查（通常游戏评分应该在 0-10 之间）
            abnormal_scores = db.query(func.count(Game.id)).filter(
                or_(
                    Game.user_score < 0,
                    Game.user_score > 10
                )
            ).scalar()
            if abnormal_scores > 0:
                print(f"⚠️  异常评分 (<0 或 >10): {abnormal_scores:>6,}")
                abnormal_list = db.query(Game.id, Game.title, Game.user_score).filter(
                    or_(Game.user_score < 0, Game.user_score > 10)
                ).limit(10).all()
                for game_id, title, score in abnormal_list:
                    print(f"    - {title[:50]:50s} 评分: {float(score):.1f}")
        else:
            print("⚠️  没有找到任何评分数据")
        
        # 认证玩家评分检查
        games_with_real_score = db.query(func.count(Game.id)).filter(
            Game.real_players_score.isnot(None)
        ).scalar()
        if games_with_real_score > 0:
            real_score_stats = db.query(
                func.min(Game.real_players_score).label('min'),
                func.max(Game.real_players_score).label('max'),
                func.avg(Game.real_players_score).label('avg')
            ).filter(Game.real_players_score.isnot(None)).first()
            print(f"有认证玩家评分:     {games_with_real_score:>6,} ({games_with_real_score/games_count*100:.1f}%)")
            print(f"认证评分范围:       {float(real_score_stats.min):.1f} ~ {float(real_score_stats.max):.1f}")
            print(f"认证评分平均:       {float(real_score_stats.avg):.2f}")
        
        # ========== 3. 价格数据检查 ==========
        print("\n【3. 价格数据检查】")
        print("-" * 80)
        
        prices_count = db.query(func.count(GamePrice.id)).scalar()
        games_with_prices = db.query(func.count(func.distinct(GamePrice.game_id))).scalar()
        
        print(f"价格记录总数:       {prices_count:>6,}")
        print(f"有价格信息的游戏:   {games_with_prices:>6,} ({games_with_prices/games_count*100:.1f}%)")
        
        if prices_count > 0:
            # 价格统计
            price_stats = db.query(
                func.min(GamePrice.price).label('min'),
                func.max(GamePrice.price).label('max'),
                func.avg(GamePrice.price).label('avg'),
                func.count(GamePrice.id).filter(GamePrice.price.isnot(None)).label('with_price')
            ).first()
            
            if price_stats.with_price > 0:
                print(f"价格范围:           ¥{float(price_stats.min):.2f} ~ ¥{float(price_stats.max):.2f}")
                print(f"平均价格:           ¥{float(price_stats.avg):.2f}")
            
            # 免费游戏检查
            free_count = db.query(func.count(GamePrice.id)).filter(
                GamePrice.is_free == True
            ).scalar()
            print(f"免费游戏记录:       {free_count:>6,}")
            
            # 异常价格检查（价格应该 >= 0）
            abnormal_prices = db.query(func.count(GamePrice.id)).filter(
                and_(
                    GamePrice.price.isnot(None),
                    GamePrice.price < 0
                )
            ).scalar()
            if abnormal_prices > 0:
                print(f"⚠️  异常价格 (<0):    {abnormal_prices:>6,}")
            
            # 价格逻辑检查（原价应该 >= 现价）
            price_logic_errors = db.execute(text("""
                SELECT COUNT(*) 
                FROM game_prices 
                WHERE price IS NOT NULL 
                  AND price_original IS NOT NULL 
                  AND price > price_original
            """)).scalar()
            if price_logic_errors > 0:
                print(f"⚠️  价格逻辑错误 (现价>原价): {price_logic_errors:>6,}")
            
            # 折扣率检查（应该在 0-100% 之间）
            sale_rate_errors = db.execute(text("""
                SELECT COUNT(*) 
                FROM game_prices 
                WHERE sale_price_rate IS NOT NULL 
                  AND (sale_price_rate < 0 OR sale_price_rate > 100)
            """)).scalar()
            if sale_rate_errors > 0:
                print(f"⚠️  异常折扣率:       {sale_rate_errors:>6,}")
            
            # 平台价格分布
            print(f"\n各平台价格记录数:")
            platform_prices = db.query(
                GamePrice.platform_name,
                func.count(GamePrice.id).label('count')
            ).group_by(GamePrice.platform_name).order_by(func.count(GamePrice.id).desc()).all()
            
            for platform, count in platform_prices:
                print(f"  {platform:20s} {count:>6,}")
        else:
            print("⚠️  没有找到任何价格数据")
        
        # ========== 4. 评论数据检查 ==========
        print("\n【4. 评论数据检查】")
        print("-" * 80)
        
        reviews_count = db.query(func.count(Review.id)).scalar()
        games_with_reviews = db.query(func.count(func.distinct(Review.game_id))).scalar()
        
        print(f"评论总数:           {reviews_count:>6,}")
        print(f"有评论的游戏:       {games_with_reviews:>6,} ({games_with_reviews/games_count*100:.1f}%)")
        
        if reviews_count > 0:
            # 评论评分检查
            reviews_with_rating = db.query(func.count(Review.id)).filter(
                Review.rating.isnot(None)
            ).scalar()
            
            if reviews_with_rating > 0:
                review_rating_stats = db.query(
                    func.min(Review.rating).label('min'),
                    func.max(Review.rating).label('max'),
                    func.avg(Review.rating).label('avg')
                ).filter(Review.rating.isnot(None)).first()
                
                print(f"有评分的评论:       {reviews_with_rating:>6,} ({reviews_with_rating/reviews_count*100:.1f}%)")
                print(f"评论评分范围:       {float(review_rating_stats.min):.1f} ~ {float(review_rating_stats.max):.1f}")
                print(f"平均评论评分:       {float(review_rating_stats.avg):.2f}")
                
                # 异常评论评分（通常应该在 0-10 之间）
                abnormal_review_ratings = db.query(func.count(Review.id)).filter(
                    or_(
                        Review.rating < 0,
                        Review.rating > 10
                    )
                ).scalar()
                if abnormal_review_ratings > 0:
                    print(f"⚠️  异常评论评分:     {abnormal_review_ratings:>6,}")
            
            # 缺失内容的评论
            missing_content = db.query(func.count(Review.id)).filter(
                or_(Review.content.is_(None), Review.content == "")
            ).scalar()
            if missing_content > 0:
                print(f"⚠️  缺失评论内容:     {missing_content:>6,} ({missing_content/reviews_count*100:.1f}%)")
            
            # 缺失作者信息的评论
            missing_author = db.query(func.count(Review.id)).filter(
                Review.author_name.is_(None)
            ).scalar()
            if missing_author > 0:
                print(f"缺失作者信息:       {missing_author:>6,} ({missing_author/reviews_count*100:.1f}%)")
            
            # 评论数量分布
            avg_reviews_per_game = reviews_count / games_with_reviews if games_with_reviews > 0 else 0
            print(f"平均每游戏评论数:   {avg_reviews_per_game:.1f}")
            
            # 评论最多的游戏
            top_reviewed = db.query(
                Review.game_id,
                func.count(Review.id).label('count')
            ).group_by(Review.game_id).order_by(func.count(Review.id).desc()).limit(5).all()
            
            if top_reviewed:
                print(f"\n评论最多的游戏 (Top 5):")
                for game_id, count in top_reviewed:
                    game = db.query(Game).filter(Game.id == game_id).first()
                    title = game.title if game else f"ID:{game_id}"
                    print(f"  {title[:50]:50s} {count:>6,} 条评论")
        else:
            print("⚠️  没有找到任何评论数据")
        
        # ========== 5. 媒体评分检查 ==========
        print("\n【5. 媒体评分检查】")
        print("-" * 80)
        
        media_scores_count = db.query(func.count(GameMediaScore.id)).scalar()
        games_with_media_scores = db.query(func.count(func.distinct(GameMediaScore.game_id))).scalar()
        
        print(f"媒体评分记录数:     {media_scores_count:>6,}")
        print(f"有媒体评分的游戏:   {games_with_media_scores:>6,} ({games_with_media_scores/games_count*100:.1f}%)")
        
        if media_scores_count > 0:
            # 媒体评分统计
            media_score_stats = db.query(
                func.min(GameMediaScore.score).label('min'),
                func.max(GameMediaScore.score).label('max'),
                func.avg(GameMediaScore.score).label('avg')
            ).filter(GameMediaScore.score.isnot(None)).first()
            
            if media_score_stats.min is not None:
                print(f"媒体评分范围:       {float(media_score_stats.min):.2f} ~ {float(media_score_stats.max):.2f}")
                print(f"平均媒体评分:       {float(media_score_stats.avg):.2f}")
            
            # 检查评分制式分布
            score_systems = db.execute(text("""
                SELECT 
                    CASE 
                        WHEN total_score = 10 THEN '10分制'
                        WHEN total_score = 100 THEN '100分制'
                        WHEN total_score IS NULL THEN '未指定'
                        ELSE '其他'
                    END as system,
                    COUNT(*) as count
                FROM game_media_scores
                GROUP BY system
                ORDER BY count DESC
            """)).fetchall()
            
            print(f"\n评分制式分布:")
            for system, count in score_systems:
                print(f"  {system:15s} {count:>6,}")
            
            # 异常媒体评分检查（根据 total_score 判断）
            # 1. 评分为负数
            negative_scores = db.query(func.count(GameMediaScore.id)).filter(
                GameMediaScore.score < 0
            ).scalar()
            
            # 2. 评分超过总分
            score_exceeds_total = db.execute(text("""
                SELECT COUNT(*) 
                FROM game_media_scores 
                WHERE score IS NOT NULL 
                  AND total_score IS NOT NULL 
                  AND score > total_score
            """)).scalar()
            
            # 3. 评分超过合理范围（假设最大是 100 分制）
            excessive_scores = db.query(func.count(GameMediaScore.id)).filter(
                GameMediaScore.score > 100
            ).scalar()
            
            # 4. 有评分但没有总分
            score_without_total = db.query(func.count(GameMediaScore.id)).filter(
                and_(
                    GameMediaScore.score.isnot(None),
                    GameMediaScore.total_score.is_(None)
                )
            ).scalar()
            
            total_abnormal = negative_scores + score_exceeds_total + excessive_scores
            if total_abnormal > 0:
                print(f"\n⚠️  异常媒体评分详情:")
                if negative_scores > 0:
                    print(f"    负分:           {negative_scores:>6,}")
                if score_exceeds_total > 0:
                    print(f"    评分超过总分:   {score_exceeds_total:>6,}")
                if excessive_scores > 0:
                    print(f"    评分超过100:    {excessive_scores:>6,}")
                if score_without_total > 0:
                    print(f"    有评分无总分:   {score_without_total:>6,}")
            
            # 媒体分布
            print(f"\n各媒体评分记录数:")
            media_stats = db.query(
                GameMediaScore.media_name,
                func.count(GameMediaScore.id).label('count')
            ).group_by(GameMediaScore.media_name).order_by(func.count(GameMediaScore.id).desc()).limit(10).all()
            
            for media, count in media_stats:
                print(f"  {media:30s} {count:>6,}")
        else:
            print("⚠️  没有找到任何媒体评分数据")
        
        # ========== 6. 榜单关联检查 ==========
        print("\n【6. 榜单关联检查】")
        print("-" * 80)
        
        rank_relations_count = db.query(func.count(GameRankRelation.id)).scalar()
        games_with_ranks = db.query(func.count(func.distinct(GameRankRelation.game_id))).scalar()
        
        print(f"榜单关联记录数:     {rank_relations_count:>6,}")
        print(f"有榜单关联的游戏:   {games_with_ranks:>6,} ({games_with_ranks/games_count*100:.1f}%)")
        
        if rank_relations_count > 0:
            # 榜单分布
            print(f"\n各榜单游戏数 (Top 10):")
            rank_stats = db.query(
                GameRankRelation.rank_id,
                func.count(GameRankRelation.id).label('count')
            ).group_by(GameRankRelation.rank_id).order_by(func.count(GameRankRelation.id).desc()).limit(10).all()
            
            for rank_id, count in rank_stats:
                print(f"  榜单 {rank_id:>4d}: {count:>6,} 个游戏")
        else:
            print("⚠️  没有找到任何榜单关联数据")
        
        # ========== 7. 数据关联完整性检查 ==========
        print("\n【7. 数据关联完整性检查】")
        print("-" * 80)
        
        # 检查孤立记录（关联表中引用的 game_id 在 games 表中不存在）
        orphaned_prices = db.execute(text("""
            SELECT COUNT(*) 
            FROM game_prices gp
            LEFT JOIN games g ON gp.game_id = g.id
            WHERE g.id IS NULL
        """)).scalar()
        
        orphaned_reviews = db.execute(text("""
            SELECT COUNT(*) 
            FROM reviews r
            LEFT JOIN games g ON r.game_id = g.id
            WHERE g.id IS NULL
        """)).scalar()
        
        orphaned_media_scores = db.execute(text("""
            SELECT COUNT(*) 
            FROM game_media_scores gms
            LEFT JOIN games g ON gms.game_id = g.id
            WHERE g.id IS NULL
        """)).scalar()
        
        orphaned_rank_relations = db.execute(text("""
            SELECT COUNT(*) 
            FROM game_rank_relations grr
            LEFT JOIN games g ON grr.game_id = g.id
            WHERE g.id IS NULL
        """)).scalar()
        
        if orphaned_prices > 0:
            print(f"⚠️  孤立的价格记录:   {orphaned_prices:>6,}")
        if orphaned_reviews > 0:
            print(f"⚠️  孤立的评论记录:   {orphaned_reviews:>6,}")
        if orphaned_media_scores > 0:
            print(f"⚠️  孤立的媒体评分:   {orphaned_media_scores:>6,}")
        if orphaned_rank_relations > 0:
            print(f"⚠️  孤立的榜单关联:   {orphaned_rank_relations:>6,}")
        
        if orphaned_prices == 0 and orphaned_reviews == 0 and orphaned_media_scores == 0 and orphaned_rank_relations == 0:
            print("✓ 所有关联数据都正确关联到游戏")
        
        # ========== 8. 数据覆盖率总结 ==========
        print("\n【8. 数据覆盖率总结】")
        print("-" * 80)
        
        coverage = {
            "有描述": (games_count - missing_description) / games_count * 100 if games_count > 0 else 0,
            "有评分": games_with_score / games_count * 100 if games_count > 0 else 0,
            "有价格": games_with_prices / games_count * 100 if games_count > 0 else 0,
            "有评论": games_with_reviews / games_count * 100 if games_count > 0 else 0,
            "有媒体评分": games_with_media_scores / games_count * 100 if games_count > 0 else 0,
            "有榜单关联": games_with_ranks / games_count * 100 if games_count > 0 else 0,
        }
        
        for key, value in coverage.items():
            status = "✓" if value >= 80 else "⚠️" if value >= 50 else "✗"
            print(f"{status} {key:15s} {value:>6.1f}%")
        
        # ========== 9. 异常数据汇总 ==========
        print("\n【9. 异常数据汇总】")
        print("-" * 80)
        
        total_issues = (
            missing_title + missing_external_id + missing_description + missing_platforms +
            (abnormal_scores if 'abnormal_scores' in locals() else 0) +
            (abnormal_prices if 'abnormal_prices' in locals() else 0) +
            (price_logic_errors if 'price_logic_errors' in locals() else 0) +
            (sale_rate_errors if 'sale_rate_errors' in locals() else 0) +
            (abnormal_review_ratings if 'abnormal_review_ratings' in locals() else 0) +
            (abnormal_media_scores if 'abnormal_media_scores' in locals() else 0) +
            orphaned_prices + orphaned_reviews + orphaned_media_scores + orphaned_rank_relations
        )
        
        if total_issues == 0:
            print("✓ 未发现异常数据")
        else:
            print(f"⚠️  发现 {total_issues:,} 个潜在问题，请检查上述详细信息")
        
        print("\n" + "=" * 80)
        print("数据校对完成！")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    check_data_quality()
