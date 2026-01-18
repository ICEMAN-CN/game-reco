# -*- coding: utf-8 -*-
"""
检查数据库表是否存在
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from sqlalchemy import inspect, text


def check_tables():
    """检查所有必需的表是否存在"""
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        # 明确指定检查 public schema
        existing_tables = set(inspector.get_table_names(schema='public'))
        
        # 必需的表
        required_tables = {
            "games": "002_create_games_table.sql",
            "game_embeddings": "004_create_game_embeddings_table.sql",
            "game_rank_relations": "005_create_game_relations_tables.sql",
            "game_prices": "005_create_game_relations_tables.sql",
            "game_media_scores": "005_create_game_relations_tables.sql",
            "reviews": "006_create_reviews_table.sql",
        }
        
        print("=" * 60)
        print("数据库表检查结果")
        print("=" * 60)
        
        missing_tables = []
        for table_name, sql_file in required_tables.items():
            if table_name in existing_tables:
                print(f"✓ {table_name:30s} - 存在")
            else:
                print(f"✗ {table_name:30s} - 缺失 (需要执行: {sql_file})")
                missing_tables.append((table_name, sql_file))
        
        print("=" * 60)
        
        if missing_tables:
            print(f"\n⚠️  发现 {len(missing_tables)} 个缺失的表！")
            print("\n请按以下顺序执行 SQL 文件：\n")
            
            # 按 SQL 文件分组
            sql_files = {}
            for table_name, sql_file in missing_tables:
                if sql_file not in sql_files:
                    sql_files[sql_file] = []
                sql_files[sql_file].append(table_name)
            
            # 按执行顺序列出
            execution_order = [
                "002_create_games_table.sql",
                "004_create_game_embeddings_table.sql",
                "006_create_reviews_table.sql",
                "005_create_game_relations_tables.sql",
            ]
            
            for sql_file in execution_order:
                if sql_file in sql_files:
                    print(f"执行: database/init/{sql_file}")
                    print(f"  创建表: {', '.join(sql_files[sql_file])}")
                    print()
            
            print("或者直接执行: database/schema.sql")
        else:
            print("\n✓ 所有必需的表都已存在！")
        
        # 检查表记录数
        print("\n" + "=" * 60)
        print("表记录数统计")
        print("=" * 60)
        for table_name in sorted(existing_tables):
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"{table_name:30s} - {count:>10,} 条记录")
            except Exception as e:
                print(f"{table_name:30s} - 查询失败: {str(e)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_tables()

