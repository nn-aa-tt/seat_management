# generate_qrcodes.py
import qrcode
import os

# --- 設定 ---
# このIPアドレスは、サーバーを動かすPCのIPアドレスに書き換えてください。
# （スマホからアクセスするために必要です）
PC_IP_ADDRESS = '172.30.53.166' # 例: ipconfig や ifconfig で調べた値
PORT = 5001
NUMBER_OF_SEATS = 320 # init_db.py と同じ値

# qrcodes フォルダがなければ作成
if not os.path.exists('qrcodes'):
    os.makedirs('qrcodes')

print(f"{NUMBER_OF_SEATS}個のQRコードを生成します...")

for i in range(1, NUMBER_OF_SEATS + 1):
    url = f"http://{PC_IP_ADDRESS}:{PORT}/seat/{i}"
    img = qrcode.make(url)
    file_path = f"qrcodes/seat_{i}.png"
    img.save(file_path)

print("QRコードの生成が完了しました。'qrcodes' フォルダを確認してください。")