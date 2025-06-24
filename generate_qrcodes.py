
import qrcode
import os


PC_IP_ADDRESS = '172.30.53.166' 
PORT = 5001
NUMBER_OF_SEATS = 320 


if not os.path.exists('qrcodes'):
    os.makedirs('qrcodes')

print(f"{NUMBER_OF_SEATS}個のQRコードを生成します...")

for i in range(1, NUMBER_OF_SEATS + 1):
    url = f"http://{PC_IP_ADDRESS}:{PORT}/seat/{i}"
    img = qrcode.make(url)
    file_path = f"qrcodes/seat_{i}.png"
    img.save(file_path)

print("QRコードの生成が完了しました。'qrcodes' フォルダを確認してください。")
