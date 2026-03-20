#!/usr/bin/env python3
"""
修复知识库外键约束问题

此脚本用于诊断和修复 knowledge_relation 表中的外键约束错误。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'arc_logi_chat'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        yield connection
    finally:
        connection.close()

def diagnose_foreign_key_issues():
    """诊断外键约束问题"""
    print("=" * 60)
    print("知识库外键约束诊断")
    print("=" * 60)
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            issues = []
            
            # 1. 检查 knowledge_relation 中引用不存在的 knowledge_item 的记录
            print("\n[1] 检查 knowledge_relation 中的孤立记录...")
            
            # 检查 source_item_id 无效的记录
            cursor.execute("""
                SELECT kr.id, kr.source_item_id, kr.target_item_id, kr.knowledge_base_id
                FROM knowledge_relation kr
                LEFT JOIN knowledge_item ki_source ON kr.source_item_id = ki_source.id
                WHERE kr.source_item_id IS NOT NULL AND ki_source.id IS NULL
            """)
            orphan_source = cursor.fetchall()
            
            if orphan_source:
                print(f"   ⚠️ 发现 {len(orphan_source)} 条记录 source_item_id 无效:")
                for row in orphan_source[:10]:
                    print(f"      - Relation ID: {row['id']}, 无效 source_item_id: {row['source_item_id']}")
                issues.extend([('source', r) for r in orphan_source])
            else:
                print("   ✅ 所有 source_item_id 引用有效")
            
            # 检查 target_item_id 无效的记录
            cursor.execute("""
                SELECT kr.id, kr.source_item_id, kr.target_item_id, kr.knowledge_base_id
                FROM knowledge_relation kr
                LEFT JOIN knowledge_item ki_target ON kr.target_item_id = ki_target.id
                WHERE kr.target_item_id IS NOT NULL AND ki_target.id IS NULL
            """)
            orphan_target = cursor.fetchall()
            
            if orphan_target:
                print(f"   ⚠️ 发现 {len(orphan_target)} 条记录 target_item_id 无效:")
                for row in orphan_target[:10]:
                    print(f"      - Relation ID: {row['id']}, 无效 target_item_id: {row['target_item_id']}")
                issues.extend([('target', r) for r in orphan_target])
            else:
                print("   ✅ 所有 target_item_id 引用有效")
            
            # 2. 检查 knowledge_relation 中 knowledge_base_id 不匹配的情况
            print("\n[2] 检查 knowledge_base_id 不匹配的记录...")
            
            cursor.execute("""
                SELECT kr.id, kr.knowledge_base_id, ki.knowledge_base_id as item_kb_id
                FROM knowledge_relation kr
                JOIN knowledge_item ki ON kr.source_item_id = ki.id
                WHERE kr.knowledge_base_id != ki.knowledge_base_id
                LIMIT 10
            """)
            kb_mismatch_source = cursor.fetchall()
            
            if kb_mismatch_source:
                print(f"   ⚠️ 发现 {len(kb_mismatch_source)} 条记录 knowledge_base_id 与 source_item 不匹配")
                for row in kb_mismatch_source[:5]:
                    print(f"      - Relation ID: {row['id']}, kr.kb_id={row['knowledge_base_id']}, item.kb_id={row['item_kb_id']}")
            
            # 3. 检查重复关系
            print("\n[3] 检查重复关系...")
            
            cursor.execute("""
                SELECT knowledge_base_id, source_item_id, target_item_id, relation_type, COUNT(*) as cnt
                FROM knowledge_relation
                GROUP BY knowledge_base_id, source_item_id, target_item_id, relation_type
                HAVING cnt > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"   ⚠️ 发现 {len(duplicates)} 组重复关系:")
                for row in duplicates[:10]:
                    print(f"      - {row['source_item_id']} -> {row['target_item_id']} ({row['relation_type']}): {row['cnt']} 次")
            else:
                print("   ✅ 无重复关系")
            
            # 4. 统计概览
            print("\n[4] 数据统计:")
            cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_relation")
            rel_count = cursor.fetchone()['cnt']
            print(f"   - knowledge_relation 记录数: {rel_count}")
            
            cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_item")
            item_count = cursor.fetchone()['cnt']
            print(f"   - knowledge_item 记录数: {item_count}")
            
            return issues

def fix_foreign_key_issues(dry_run=True):
    """修复外键约束问题
    
    Args:
        dry_run: 如果为 True，只报告问题而不实际修复
    """
    print("\n" + "=" * 60)
    print("修复外键约束问题" + (" (模拟模式)" if dry_run else ""))
    print("=" * 60)
    
    if dry_run:
        print("\n⚠️  运行在模拟模式，不会实际修改数据")
        print("   使用 --fix 参数实际执行修复")
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            # 1. 删除 source_item_id 无效的记录
            print("\n[1] 删除 source_item_id 无效的记录...")
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM knowledge_relation kr
                LEFT JOIN knowledge_item ki_source ON kr.source_item_id = ki_source.id
                WHERE kr.source_item_id IS NOT NULL AND ki_source.id IS NULL
            """)
            count = cursor.fetchone()['cnt']
            
            if count > 0:
                if dry_run:
                    print(f"   将删除 {count} 条记录")
                else:
                    cursor.execute("""
                        DELETE kr FROM knowledge_relation kr
                        LEFT JOIN knowledge_item ki_source ON kr.source_item_id = ki_source.id
                        WHERE kr.source_item_id IS NOT NULL AND ki_source.id IS NULL
                    """)
                    conn.commit()
                    print(f"   ✅ 已删除 {count} 条记录")
            else:
                print("   ✅ 无需删除")
            
            # 2. 删除 target_item_id 无效的记录
            print("\n[2] 删除 target_item_id 无效的记录...")
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM knowledge_relation kr
                LEFT JOIN knowledge_item ki_target ON kr.target_item_id = ki_target.id
                WHERE kr.target_item_id IS NOT NULL AND ki_target.id IS NULL
            """)
            count = cursor.fetchone()['cnt']
            
            if count > 0:
                if dry_run:
                    print(f"   将删除 {count} 条记录")
                else:
                    cursor.execute("""
                        DELETE kr FROM knowledge_relation kr
                        LEFT JOIN knowledge_item ki_target ON kr.target_item_id = ki_target.id
                        WHERE kr.target_item_id IS NOT NULL AND ki_target.id IS NULL
                    """)
                    conn.commit()
                    print(f"   ✅ 已删除 {count} 条记录")
            else:
                print("   ✅ 无需删除")
            
            # 3. 修复 knowledge_base_id 不匹配的问题
            print("\n[3] 修复 knowledge_base_id 不匹配的问题...")
            
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM knowledge_relation kr
                JOIN knowledge_item ki ON (kr.source_item_id = ki.id OR kr.target_item_id = ki.id)
                AND kr.knowledge_base_id != ki.knowledge_base_id
            """)
            count = cursor.fetchone()['cnt']
            
            if count > 0:
                if dry_run:
                    print(f"   将修复 {count} 条记录")
                    print("   注意: 此类问题需要人工判断如何处理")
                else:
                    print("   ⚠️ 此类问题需要人工判断，建议手动处理")
                    print(f"   受影响记录数: {count}")
            else:
                print("   ✅ 无需修复")
            
            # 4. 删除重复关系（保留最小的 ID）
            print("\n[4] 删除重复关系...")
            cursor.execute("""
                SELECT MIN(id) as keep_id,
                       knowledge_base_id, source_item_id, target_item_id, relation_type
                FROM knowledge_relation
                GROUP BY knowledge_base_id, source_item_id, target_item_id, relation_type
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            total_dup_count = 0
            for dup in duplicates:
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM knowledge_relation
                    WHERE knowledge_base_id = %s 
                    AND source_item_id = %s 
                    AND target_item_id = %s 
                    AND relation_type = %s
                """, (dup['knowledge_base_id'], dup['source_item_id'], dup['target_item_id'], dup['relation_type']))
                total_count = cursor.fetchone()['cnt']
                total_dup_count += total_count - 1
            
            if total_dup_count > 0:
                if dry_run:
                    print(f"   将删除 {total_dup_count} 条重复记录")
                else:
                    cursor.execute("""
                        DELETE kr FROM knowledge_relation kr
                        INNER JOIN (
                            SELECT MIN(id) as keep_id,
                                   knowledge_base_id, source_item_id, target_item_id, relation_type
                            FROM knowledge_relation
                            GROUP BY knowledge_base_id, source_item_id, target_item_id, relation_type
                            HAVING COUNT(*) > 1
                        ) dup ON kr.knowledge_base_id = dup.knowledge_base_id
                              AND COALESCE(kr.source_item_id, 0) = COALESCE(dup.source_item_id, 0)
                              AND kr.target_item_id = dup.target_item_id
                              AND kr.relation_type = dup.relation_type
                              AND kr.id > dup.keep_id
                    """)
                    conn.commit()
                    print(f"   ✅ 已删除 {total_dup_count} 条重复记录")
            else:
                print("   ✅ 无重复关系")
    
    print("\n" + "=" * 60)

def verify_and_repair_constraints():
    """验证并修复外键约束定义"""
    print("\n" + "=" * 60)
    print("验证外键约束定义")
    print("=" * 60)
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            # 检查 knowledge_relation 表的外键约束
            print("\n[1] 检查 knowledge_relation 表的外键约束...")
            cursor.execute("""
                SELECT 
                    CONSTRAINT_NAME,
                    TABLE_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'knowledge_relation'
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            constraints = cursor.fetchall()
            
            if constraints:
                print("   当前外键约束:")
                for c in constraints:
                    print(f"   - {c['CONSTRAINT_NAME']}: {c['TABLE_NAME']}.{c['COLUMN_NAME']} -> {c['REFERENCED_TABLE_NAME']}.{c['REFERENCED_COLUMN_NAME']}")
            else:
                print("   ⚠️ knowledge_relation 表没有 source_item_id 和 target_item_id 的外键约束！")
                print("   这可能导致数据不一致问题。")
                print("\n   要添加外键约束，执行以下 SQL:")
                print("""
   ALTER TABLE knowledge_relation 
   ADD CONSTRAINT fk_kr_source_item 
   FOREIGN KEY (source_item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE,
   ADD CONSTRAINT fk_kr_target_item 
   FOREIGN KEY (target_item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE;
                """)
            
            print("\n[2] 建议的预防措施:")
            print("   1. 使用 ON DELETE CASCADE 确保删除知识条目时自动清理关系")
            print("   2. 在插入关系前验证条目是否存在")
            print("   3. 定期运行数据一致性检查")
            print("   4. 使用唯一约束防止重复关系")

def migrate_tag_relations(dry_run=True):
    """迁移 tag 类型关系到新的 knowledge_item_tag 表"""
    print("\n" + "=" * 60)
    print("迁移标签关系" + (" (模拟模式)" if dry_run else ""))
    print("=" * 60)
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            print("\n[1] 创建 knowledge_item_tag 表（如不存在）...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item_tag (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT NOT NULL,
                    tag_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_item_tag (item_id, tag_id),
                    INDEX idx_tag (tag_id),
                    FOREIGN KEY (item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES knowledge_tag(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            if not dry_run:
                conn.commit()
            print("   ✅ 表已准备好")
            
            print("\n[2] 查找需要迁移的 tag 类型关系...")
            cursor.execute("""
                SELECT kr.id, kr.source_item_id, kr.target_item_id, kr.knowledge_base_id,
                       kt.name as tag_name
                FROM knowledge_relation kr
                JOIN knowledge_tag kt ON kr.target_item_id = kt.id
                WHERE kr.relation_type = 'tag'
            """)
            tag_relations = cursor.fetchall()
            
            if not tag_relations:
                print("   ✅ 没有需要迁移的 tag 类型关系")
                return
            
            print(f"   发现 {len(tag_relations)} 条 tag 类型关系需要迁移")
            
            for rel in tag_relations[:10]:
                print(f"   - Relation ID: {rel['id']}, item={rel['source_item_id']}, tag={rel['target_item_id']} ({rel['tag_name']})")
            
            if dry_run:
                print(f"\n   将迁移 {len(tag_relations)} 条记录到 knowledge_item_tag 表")
            else:
                print("\n[3] 执行迁移...")
                migrated = 0
                for rel in tag_relations:
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO knowledge_item_tag (item_id, tag_id)
                            VALUES (%s, %s)
                        """, (rel['source_item_id'], rel['target_item_id']))
                        if cursor.rowcount > 0:
                            migrated += 1
                            cursor.execute("""
                                UPDATE knowledge_tag SET usage_count = usage_count + 1 WHERE id = %s
                            """, (rel['target_item_id'],))
                    except Exception as e:
                        print(f"   ⚠️ 迁移 Relation ID {rel['id']} 失败: {e}")
                
                conn.commit()
                print(f"   ✅ 已迁移 {migrated} 条记录")
                
                print("\n[4] 删除已迁移的 tag 类型关系...")
                cursor.execute("""
                    DELETE FROM knowledge_relation WHERE relation_type = 'tag'
                """)
                conn.commit()
                print(f"   ✅ 已删除 {cursor.rowcount} 条 tag 类型关系")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='修复知识库外键约束问题')
    parser.add_argument('--fix', action='store_true', help='实际执行修复（默认只报告问题）')
    parser.add_argument('--verify', action='store_true', help='验证外键约束定义')
    parser.add_argument('--migrate-tags', action='store_true', help='迁移标签关系到新表')
    args = parser.parse_args()
    
    if args.verify:
        verify_and_repair_constraints()
    elif args.migrate_tags:
        migrate_tag_relations(dry_run=not args.fix)
        if not args.fix:
            print("\n使用 --fix 参数实际执行迁移")
    else:
        diagnose_foreign_key_issues()
        if args.fix:
            confirm = input("\n确认执行修复操作? (yes/no): ")
            if confirm.lower() == 'yes':
                fix_foreign_key_issues(dry_run=False)
            else:
                print("已取消修复操作")
        else:
            print("\n使用 --fix 参数执行实际修复")
            print("使用 --verify 参数验证外键约束定义")
            print("使用 --migrate-tags 参数迁移标签关系")
