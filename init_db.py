# init_db.py
import sqlite3

# --- 設定 ---
DB_NAME = 'seats.db'
NUMBER_OF_SEATS = 320 # generate_svg.py で生成される総座席数と合わせる

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS seats')
cursor.execute('''
CREATE TABLE seats (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL,
    timestamp TEXT
)
''')
print(f"テーブル 'seats' を作成しました。")

for i in range(1, NUMBER_OF_SEATS + 1):
    cursor.execute("INSERT INTO seats (id, status, timestamp) VALUES (?, ?, ?)",
                   (i, 'available', None))

print(f"{NUMBER_OF_SEATS} 個の座席を初期状態 'available' で登録しました。")

conn.commit()
conn.close()
print("データベースの初期化が完了しました。")