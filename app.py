import os
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, jsonify, redirect, url_for, request,
                   session, flash)
from sqlalchemy import create_engine, text

app = Flask(__name__)

EXPIRATION_MINUTES = 20


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'local-dev-secret-key-you-can-change') 
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'local-admin-pass') 

db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
   
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)
else:
    engine = create_engine("sqlite:///seats.db")


def check_seat_expiry():
    """一定時間経過した席を自動で空席に戻す"""
    while True:
        time.sleep(60)
        with app.app_context():
            try:
                with engine.connect() as conn:
                    taken_seats = conn.execute(text("SELECT id, timestamp FROM seats WHERE status = 'taken' AND timestamp IS NOT NULL")).fetchall()
                    
                    for seat in taken_seats:
                        timestamp = datetime.fromisoformat(seat[1])
                        if datetime.now() > timestamp + timedelta(minutes=EXPIRATION_MINUTES):
                            # 時間が超過した席を空席に戻す
                            conn.execute(text(
                                "UPDATE seats SET status = 'available', timestamp = NULL WHERE id = :id"
                            ), {"id": seat[0]})
                            conn.commit()
                            print(f"座席 {seat[0]} を自動的に空席に戻しました。")
            except Exception as e:
                print(f"有効期限チェック中にエラーが発生しました: {e}")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('このページにアクセスするにはログインが必要です。', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/')
def index():
    """メインの座席表ページ"""
    with engine.connect() as conn:
        total_seats = conn.execute(text('SELECT COUNT(id) FROM seats')).scalar() or 0
    return render_template('index.html', total_seats=total_seats)

@app.route('/seat/<int:seat_id>')
def take_seat(seat_id):
    """QRコードからアクセスされ、席を「使用中」にする"""
    with engine.connect() as conn:
        conn.execute(text(
            "UPDATE seats SET status = :status, timestamp = :timestamp WHERE id = :id"
        ), {
            "status": 'taken', 
            "timestamp": datetime.now().isoformat(), 
            "id": seat_id
        })
        conn.commit()
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    """JavaScriptが座席状況を取得するためのAPI"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, status FROM seats"))
        current_statuses = {row['id']: row['status'] for row in result.mappings().all()}
    return jsonify(current_statuses)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理者ログインページ"""
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('ログインに成功しました！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('パスワードが間違っています。', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    """管理者用ダッシュボード"""
    with engine.connect() as conn:
        all_seats_data = conn.execute(text("SELECT id, status, timestamp FROM seats ORDER BY id")).mappings().all()
    return render_template('admin_dashboard.html', seats=all_seats_data)

@app.route('/admin/update/<int:seat_id>/<string:new_status>')
@login_required
def admin_update_status(seat_id, new_status):
    """管理者が手動で座席ステータスを更新する"""
    with engine.connect() as conn:
        if new_status == 'available':
            conn.execute(text(
                "UPDATE seats SET status = 'available', timestamp = NULL WHERE id = :id"
            ), {"id": seat_id})
        elif new_status == 'taken':
            conn.execute(text(
                "UPDATE seats SET status = 'taken', timestamp = :timestamp WHERE id = :id"
            ), {"id": seat_id, "timestamp": datetime.now().isoformat()})
        conn.commit()
    flash(f"座席 {seat_id} の状態を更新しました。", 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    """管理者ログアウト"""
    session.pop('logged_in', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('admin_login'))


expiry_thread = threading.Thread(target=check_seat_expiry, daemon=True)
expiry_thread.start()


if __name__ == '__main__':
    
    print("ローカル開発サーバーを起動します...")
    app.run(host='0.0.0.0', port=5001)
