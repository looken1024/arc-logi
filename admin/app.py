from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import secrets
import subprocess
import shlex

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = None

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

COMMAND_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'command_history.json')

def load_command_history():
    if os.path.exists(COMMAND_HISTORY_FILE):
        try:
            with open(COMMAND_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_command_history(history):
    with open(COMMAND_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('cmd.html')

@app.route('/login')
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': '请输入用户名和密码'})
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['username'] = username
        session.permanent = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '用户名或密码错误'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check_login', methods=['GET'])
def check_login():
    if 'username' in session:
        return jsonify({'success': True, 'username': session['username']})
    return jsonify({'success': False})

@app.route('/api/execute', methods=['POST'])
def execute_command():
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json()
    command = data.get('command', '').strip()
    workdir = data.get('workdir', '').strip() or os.getcwd()
    
    if not command:
        return jsonify({'success': False, 'error': '请输入命令'})
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout if result.stdout else ''
        error = result.stderr if result.stderr else ''
        
        if result.returncode != 0 and not output:
            output = error
        
        history = load_command_history()
        history.insert(0, {
            'command': command,
            'workdir': workdir,
            'output': output[:5000],
            'error': error[:1000] if error else '',
            'returncode': result.returncode,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        history = history[:100]
        save_command_history(history)
        
        return jsonify({
            'success': True,
            'output': output,
            'error': error,
            'returncode': result.returncode
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '命令执行超时（最大5分钟）'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute_stream', methods=['POST'])
def execute_command_stream():
    if 'username' not in session:
        return Response(f"data: {json.dumps({'error': '未登录'})}\n\n", mimetype='text/event-stream'), 401
    
    data = request.get_json()
    command = data.get('command', '').strip()
    workdir = data.get('workdir', '').strip() or os.getcwd()
    
    if not command:
        return Response(f"data: {json.dumps({'error': '请输入命令'})}\n\n", mimetype='text/event-stream')
    
    def generate():
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            error_lines = []
            
            import select
            
            stdout = process.stdout
            stderr = process.stderr
            
            while True:
                if stdout:
                    reads = [stdout.fileno()]
                else:
                    reads = []
                if stderr:
                    reads.append(stderr.fileno())
                
                if reads:
                    readable, _, _ = select.select(reads, [], [], 0.1)
                    
                    if stdout and stdout.fileno() in readable:
                        line = stdout.readline()
                        if line:
                            output_lines.append(line)
                            yield f"data: {json.dumps({'type': 'output', 'data': line})}\n\n"
                    
                    if stderr and stderr.fileno() in readable:
                        line = stderr.readline()
                        if line:
                            error_lines.append(line)
                            yield f"data: {json.dumps({'type': 'error', 'data': line})}\n\n"
                
                if process.poll() is not None:
                    break
            
            if stdout:
                remaining_out = stdout.read()
                if remaining_out:
                    output_lines.append(remaining_out)
                    yield f"data: {json.dumps({'type': 'output', 'data': remaining_out})}\n\n"
            if stderr:
                remaining_err = stderr.read()
                if remaining_err:
                    error_lines.append(remaining_err)
                    yield f"data: {json.dumps({'type': 'error', 'data': remaining_err})}\n\n"
            
            returncode = process.returncode
            
            yield f"data: {json.dumps({'type': 'done', 'returncode': returncode})}\n\n"
            
            output = ''.join(output_lines)
            error = ''.join(error_lines)
            
            history = load_command_history()
            history.insert(0, {
                'command': command,
                'workdir': workdir,
                'output': output[:5000],
                'error': error[:1000] if error else '',
                'returncode': returncode,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            history = history[:100]
            save_command_history(history)
            
        except subprocess.TimeoutExpired:
            yield f"data: {json.dumps({'type': 'error', 'data': '命令执行超时（最大5分钟）'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'returncode': -1})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'returncode': -1})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    history = load_command_history()
    return jsonify({'success': True, 'history': history})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    save_command_history([])
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
