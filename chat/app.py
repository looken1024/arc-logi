from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import openai
from typing import Generator
import secrets

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

# 数据存储(实际项目中应使用数据库)
users = {}  # {username: {password: hash, email: str, theme: str, created_at: str}}
conversations = {}  # {conversation_id: [messages]}
user_conversations = {}  # {username: [conversation_ids]}

@app.route('/')
def index():
    """主页 - 需要登录"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login():
    """登录页面"""
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register')
def register():
    """注册页面"""
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        # 验证
        if not username or len(username) < 3:
            return jsonify({'error': '用户名至少3个字符'}), 400
        if not password or len(password) < 6:
            return jsonify({'error': '密码至少6个字符'}), 400
        if username in users:
            return jsonify({'error': '用户名已存在'}), 400
        
        # 创建用户
        users[username] = {
            'password': generate_password_hash(password),
            'email': email,
            'theme': 'dark',  # 默认深色主题
            'created_at': datetime.now().isoformat()
        }
        user_conversations[username] = []
        
        return jsonify({'success': True, 'message': '注册成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': '请输入用户名和密码'}), 400
        
        if username not in users:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not check_password_hash(users[username]['password'], password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 设置会话
        session.permanent = True
        session['username'] = username
        
        return jsonify({
            'success': True,
            'username': username,
            'theme': users[username].get('theme', 'dark')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """用户登出"""
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/api/user', methods=['GET'])
def get_user():
    """获取当前用户信息"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    user = users.get(username, {})
    
    return jsonify({
        'username': username,
        'email': user.get('email', ''),
        'theme': user.get('theme', 'dark'),
        'created_at': user.get('created_at', '')
    })

@app.route('/api/user/theme', methods=['PUT'])
def update_theme():
    """更新用户主题"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json
        theme = data.get('theme', 'dark')
        
        if theme not in ['dark', 'light', 'blue', 'green', 'purple']:
            return jsonify({'error': '无效的主题'}), 400
        
        username = session['username']
        users[username]['theme'] = theme
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求 - 流式返回"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'default')
        model = data.get('model', 'deepseek-chat')
        username = session['username']
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 获取或创建对话历史
        if conversation_id not in conversations:
            conversations[conversation_id] = []
            # 将对话关联到用户
            if username not in user_conversations:
                user_conversations[username] = []
            if conversation_id not in user_conversations[username]:
                user_conversations[username].append(conversation_id)
        
        # 添加用户消息
        conversations[conversation_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 调用 AI API (流式)
        def generate():
            try:
                # 创建 OpenAI 客户端
                client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    timeout=60.0,
                    max_retries=2
                )
                
                messages = [
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in conversations[conversation_id]
                    if msg['role'] in ['user', 'assistant']
                ]
                
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                full_response = ''
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield f"data: {json.dumps({'content': content})}\n\n"
                
                # 保存完整的助手回复
                conversations[conversation_id].append({
                    'role': 'assistant',
                    'content': full_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """获取对话历史"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    # 验证对话所有权
    if conversation_id not in user_conversations.get(username, []):
        return jsonify({'error': '无权访问'}), 403
    
    if conversation_id in conversations:
        return jsonify({
            'conversation_id': conversation_id,
            'messages': conversations[conversation_id]
        })
    return jsonify({'messages': []})

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    # 验证对话所有权
    if conversation_id not in user_conversations.get(username, []):
        return jsonify({'error': '无权访问'}), 403
    
    if conversation_id in conversations:
        del conversations[conversation_id]
    if username in user_conversations and conversation_id in user_conversations[username]:
        user_conversations[username].remove(conversation_id)
    return jsonify({'success': True})

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """列出所有对话"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    conversation_list = []
    
    for conv_id in user_conversations.get(username, []):
        if conv_id in conversations:
            messages = conversations[conv_id]
            if messages:
                first_message = next((m for m in messages if m['role'] == 'user'), None)
                conversation_list.append({
                    'id': conv_id,
                    'title': first_message['content'][:50] if first_message else '新对话',
                    'updated_at': messages[-1]['timestamp'],
                    'message_count': len(messages)
                })
    
    # 按更新时间排序
    conversation_list.sort(key=lambda x: x['updated_at'], reverse=True)
    return jsonify({'conversations': conversation_list})

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = [
        {'id': 'deepseek-chat', 'name': 'DeepSeek Chat', 'description': '强大的对话模型'},
        {'id': 'deepseek-coder', 'name': 'DeepSeek Coder', 'description': '专业的编程模型'},
        {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'description': '需要 OpenAI API'},
        {'id': 'gpt-4', 'name': 'GPT-4', 'description': '需要 OpenAI API'},
    ]
    return jsonify({'models': models})

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # 确保模板目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("\n" + "="*50)
    print("🚀 AI Chat Platform Starting...")
    print("="*50)
    
    # 检查 API Key 配置
    if OPENAI_API_KEY:
        print("✅ API Key: 已配置")
        print(f"🔗 API URL: {OPENAI_BASE_URL}")
    else:
        print("⚠️  API Key: 未配置 (请在 .env 文件中设置 OPENAI_API_KEY)")
    
    print(f"📝 访问地址: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
