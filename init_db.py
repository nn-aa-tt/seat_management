import os
from sqlalchemy import create_engine, text

# RenderのDATABASE_URLを環境変数から読み込む
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("エラー: 環境変数 DATABASE_URL が設定されていません。")
    print("例: export DATABASE_URL='postgres://...'")
else:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(db_url)
    NUMBER_OF_SEATS = 194 # 現在の総座席数

    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS seats'))
        conn.execute(text('''
            CREATE TABLE seats (
                id INTEGER PRIMARY KEY,
                status VARCHAR(20) NOT NULL,
                timestamp VARCHAR(50)
            )
        '''))
        for i in range(1, NUMBER_OF_SEATS + 1):
            conn.execute(text(
                "INSERT INTO seats (id, status, timestamp) VALUES (:id, :status, :timestamp)"
            ), {"id": i, "status": 'available', "timestamp": None})
        conn.commit()
    print(f"PostgreSQLデータベースの初期化が完了しました。総座席数: {NUMBER_OF_SEATS}")