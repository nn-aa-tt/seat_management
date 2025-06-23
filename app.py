"""
seat_manager/
│
├── generate_svg.py         # 座席表のSVGファイルを自動生成する
├── init_db.py              # データベースを初期化する
├── generate_qrcodes.py     # 各座席のQRコードを生成する
├── app.py                  # メインのWebアプリケーション
├── seats.db                # データベースファイル（init_db.py実行後に生成）
│
├── templates/              # HTMLファイルなどを格納するフォルダ
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── seatmap.svg         # (generate_svg.py実行後に生成)
│
└── qrcodes/                # QRコード画像を格納するフォルダ
    ├── seat_1.png
    ├── seat_2.png
    └── ...
"""

# osライブラリをインポート
import os
from flask import Flask, render_template, jsonify, redirect, url_for, request, session, flash
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

# --- 設定 ---
DB_NAME = 'seats.db'
EXPIRATION_MINUTES = 20

# --- 【修正】秘密の情報を環境変数から読み込む ---
# RenderなどのWebサーバー上で設定した値を取得する。
# もし環境変数がなければ（ローカルでの開発中など）、後ろのデフォルト値が使われる。
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'local-dev-secret-key') 
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'local-admin-pass') 




# --- データベース接続 ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False) # check_same_thread=False を追加
    conn.row_factory = sqlite3.Row
    return conn

# --- バックグラウンド処理（変更なし）---
def check_seat_expiry():
    while True:
        time.sleep(60)
        with app.app_context(): # 【追加】バックグラウンドスレッドでFlaskの機能を使うため
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DBの有効期限をチェック中...")
            conn = get_db_connection()
            seats_to_check = conn.execute("SELECT id, timestamp FROM seats WHERE status = 'taken' AND timestamp IS NOT NULL").fetchall()
            
            for seat in seats_to_check:
                seat_id = seat['id']
                timestamp = datetime.fromisoformat(seat['timestamp'])
                if datetime.now() > timestamp + timedelta(minutes=EXPIRATION_MINUTES):
                    print(f"座席 {seat_id} の利用時間が超過。DBを更新します。")
                    conn.execute("UPDATE seats SET status = ?, timestamp = ? WHERE id = ?", ('available', None, seat_id))
                    conn.commit()
            conn.close()

# --- 【追加】ログイン必須デコレータ ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('このページにアクセスするにはログインが必要です。', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- 一般ユーザー向けページ ---
@app.route('/')
def index():
    conn = get_db_connection()
    total_seats = conn.execute('SELECT COUNT(id) FROM seats').fetchone()[0]
    conn.close()
    return render_template('index.html', total_seats=total_seats)

@app.route('/seat/<int:seat_id>')
def take_seat(seat_id):
    conn = get_db_connection()
    current_time_str = datetime.now().isoformat()
    conn.execute("UPDATE seats SET status = ?, timestamp = ? WHERE id = ?", ('taken', current_time_str, seat_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    conn = get_db_connection()
    all_seats = conn.execute("SELECT id, status FROM seats").fetchall()
    conn.close()
    current_statuses = {seat['id']: seat['status'] for seat in all_seats}
    return jsonify(current_statuses)

# --- 【ここから管理者向けページ】 ---

# 1. 管理者ログインページ
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('ログインに成功しました！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('パスワードが間違っています。', 'danger')
    return render_template('admin_login.html')

# 2. 管理者ダッシュボード
@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    all_seats_data = conn.execute("SELECT id, status, timestamp FROM seats ORDER BY id").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', seats=all_seats_data)

# 3. 座席の状態を更新するアクション
@app.route('/admin/update/<int:seat_id>/<string:new_status>')
@login_required
def admin_update_status(seat_id, new_status):
    conn = get_db_connection()
    if new_status == 'available':
        conn.execute("UPDATE seats SET status = ?, timestamp = ? WHERE id = ?", ('available', None, seat_id))
    elif new_status == 'taken':
        current_time_str = datetime.now().isoformat()
        conn.execute("UPDATE seats SET status = ?, timestamp = ? WHERE id = ?", ('taken', current_time_str, seat_id))
    
    conn.commit()
    conn.close()
    flash(f"座席 {seat_id} の状態を「{new_status}」に更新しました。", 'info')
    return redirect(url_for('admin_dashboard'))

# 4. ログアウト
@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('logged_in', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('admin_login'))

# if __name__ == '__main__':
#     expiry_thread = threading.Thread(target=check_seat_expiry, daemon=True)
#     expiry_thread.start()
#     app.run(host='0.0.0.0', port=5001, debug=False) # 本番運用に近いのでdebug=Falseを推奨