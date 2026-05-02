import serial
import time

# 設定 Arduino 的 Port (例如 Windows 是 'COM3', Mac/Linux 是 '/dev/ttyUSB0')
ser = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2) # 等待連線穩定

def check_mood_file():
    try:
        with open('setting/aila_mood.txt', 'r', encoding='utf-8') as f:
            content = f.read().lower()
            
            if "happy" in content:
                send_to_arduino("happy")
            elif "sad" in content:
                send_to_arduino("sad")
            elif "mad" in content:
                send_to_arduino("mad")
            elif "chill" in content:
                send_to_arduino("chill")
    except FileNotFoundError:
        print("找不到檔案 mood.txt")

def send_to_arduino(mood):
    print(f"偵測到情緒: {mood}")
    ser.write((mood + '\n').encode())

while True:
    check_mood_file()
    time.sleep(1) # 每 5 秒檢查一次檔案