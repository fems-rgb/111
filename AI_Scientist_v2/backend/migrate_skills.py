"""自动迁移：给 custom_skills 表加新列"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "zhixing.db")
if not os.path.exists(DB_PATH):
    DB_PATH = "zhixing.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_skills'")
if not cursor.fetchone():
    print("custom_skills 表不存在，将由 SQLAlchemy 自动创建")
    conn.close()
    exit(0)

# 获取已有列
cursor.execute("PRAGMA table_info(custom_skills)")
existing_cols = {row[1] for row in cursor.fetchall()}

new_cols = {
    "webhook_url": "VARCHAR(500) DEFAULT ''",
    "webhook_method": "VARCHAR(10) DEFAULT 'POST'",
    "linked_doc_ids": "TEXT DEFAULT '[]'",
    "linked_project_id": "INTEGER",
}

for col_name, col_def in new_cols.items():
    if col_name not in existing_cols:
        cursor.execute(f"ALTER TABLE custom_skills ADD COLUMN {col_name} {col_def}")
        print(f"  + Added column: {col_name}")
    else:
        print(f"  = Column exists: {col_name}")

# 同时把 prompt_template 从 NOT NULL 改为允许空（webhook技能不需要prompt）
# SQLite 不支持 ALTER COLUMN，跳过这步，在代码层面处理

conn.commit()
conn.close()
print("✅ 数据库迁移完成")