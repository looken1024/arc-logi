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
import pymysql
from contextlib import contextmanager

# 导入 skills 模块
from skills import register_all_skills

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'arc_logi_chat'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
    'cursorclass': pymysql.cursors.DictCursor
}

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        yield connection
    finally:
        connection.close()

def init_database():
    """初始化数据库表"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    theme VARCHAR(20) DEFAULT 'dark',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建对话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    conversation_id VARCHAR(64) NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    messages JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_conversation_id (conversation_id),
                    INDEX idx_username (username),
                    UNIQUE KEY uk_user_conv (username, conversation_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建用户技能状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    enabled TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_user_skill (username, skill_name),
                    INDEX idx_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            print("✅ 数据库表初始化完成")

# 初始化技能注册表
skill_registry = register_all_skills()

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

@app.route('/md5')
def md5_tool():
    """MD5 工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('md5.html')

@app.route('/tools')
def tools():
    """工具列表页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('tools.html')

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
        
        # 检查用户名是否已存在
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return jsonify({'error': '用户名已存在'}), 400
        
        # 创建用户
        password_hash = generate_password_hash(password)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, email, theme) VALUES (%s, %s, %s, %s)",
                    (username, password_hash, email, 'dark')
                )
                conn.commit()
        
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
        
        # 验证用户
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not check_password_hash(user['password'], password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 设置会话
        session.permanent = True
        session['username'] = username
        
        return jsonify({
            'success': True,
            'username': username,
            'theme': user.get('theme', 'dark')
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
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, email, theme, created_at FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
    
    if user:
        return jsonify({
            'username': user['username'],
            'email': user.get('email', ''),
            'theme': user.get('theme', 'dark'),
            'created_at': user.get('created_at', '').isoformat() if user.get('created_at') else ''
        })
    return jsonify({'error': '用户不存在'}), 404

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
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET theme = %s WHERE username = %s", (theme, username))
                conn.commit()
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_user_conversations(username):
    """获取用户的所有对话ID列表"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT conversation_id FROM conversations WHERE username = %s", (username,))
            results = cursor.fetchall()
            return [row['conversation_id'] for row in results]

def get_conversation_from_db(conversation_id, username):
    """从数据库获取对话"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT messages FROM conversations WHERE conversation_id = %s AND username = %s", 
                          (conversation_id, username))
            result = cursor.fetchone()
            if result and result['messages']:
                return json.loads(result['messages'])
            return []

def save_conversation_to_db(conversation_id, username, messages):
    """保存对话到数据库"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (conversation_id, username, messages) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE messages = %s, updated_at = CURRENT_TIMESTAMP",
                (conversation_id, username, json.dumps(messages, ensure_ascii=False), json.dumps(messages, ensure_ascii=False))
            )
            conn.commit()

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
        
        # 获取对话历史
        messages = get_conversation_from_db(conversation_id, username)
        
        # 添加用户消息
        messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 调用 AI API (流式)
        def generate():
            try:
                # 根据模型选择 API 地址
                if model.startswith('deepseek'):
                    base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
                else:
                    base_url = OPENAI_BASE_URL
                
                # 创建 OpenAI 客户端
                client = openai.OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=base_url,
                    timeout=60.0,
                    max_retries=2
                )
                
                # 准备消息格式
                api_messages = [
                    {'role': msg['role'], 'content': msg['content']}
                    for msg in messages
                    if msg['role'] in ['user', 'assistant']
                ]
                
                # 获取用户启用的技能函数定义
                enabled_skills = get_enabled_skills_for_user(username)
                tools = []
                for skill_name in enabled_skills:
                    skill = skill_registry.get_skill(skill_name)
                    if skill:
                        tools.append({
                            "type": "function",
                            "function": skill.to_function_definition()
                        })
                
                # 第一次 API 调用（可能触发 function calling）
                response = client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # 检查是否需要调用函数
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                full_response = ''
                
                if tool_calls:
                    # AI 决定调用技能
                    api_messages.append(response_message)
                    
                    # 执行所有被调用的技能
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # 执行技能
                        result = skill_registry.execute_skill(function_name, **function_args)
                        
                        # 将技能执行结果添加到消息中
                        api_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                    
                    # 再次调用 API 获取最终回复（流式）
                    stream = client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield f"data: {json.dumps({'content': content})}\n\n"
                else:
                    # 没有调用技能，直接流式返回
                    stream = client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield f"data: {json.dumps({'content': content})}\n\n"
                
                # 保存完整的助手回复
                messages.append({
                    'role': 'assistant',
                    'content': full_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 持久化到数据库
                save_conversation_to_db(conversation_id, username, messages)
                
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
    user_conv_ids = get_user_conversations(username)
    if conversation_id not in user_conv_ids:
        return jsonify({'error': '无权访问'}), 403
    
    messages = get_conversation_from_db(conversation_id, username)
    return jsonify({
        'conversation_id': conversation_id,
        'messages': messages
    })

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    # 验证对话所有权
    user_conv_ids = get_user_conversations(username)
    if conversation_id not in user_conv_ids:
        return jsonify({'error': '无权访问'}), 403
    
    # 从数据库删除
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM conversations WHERE conversation_id = %s AND username = %s", 
                          (conversation_id, username))
            conn.commit()
    
    return jsonify({'success': True})

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """列出所有对话"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT conversation_id, messages, updated_at FROM conversations WHERE username = %s ORDER BY updated_at DESC",
                (username,)
            )
            results = cursor.fetchall()
    
    conversation_list = []
    for row in results:
        messages = json.loads(row['messages']) if row['messages'] else []
        if messages:
            first_message = next((m for m in messages if m['role'] == 'user'), None)
            conversation_list.append({
                'id': row['conversation_id'],
                'title': first_message['content'][:50] if first_message else '新对话',
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else '',
                'message_count': len(messages)
            })
    
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

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """获取可用技能列表"""
    skills = []
    for skill_name in skill_registry.list_skills():
        skill = skill_registry.get_skill(skill_name)
        if skill:
            skills.append({
                'name': skill.name,
                'description': skill.description,
                'parameters': skill.parameters
            })
    return jsonify({
        'skills': skills,
        'count': len(skills)
    })

@app.route('/api/skills/<skill_name>', methods=['POST'])
def execute_skill_api(skill_name):
    """手动执行指定技能（用于测试）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401

    try:
        data = request.json or {}
        result = skill_registry.execute_skill(skill_name, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/skills', methods=['GET'])
def get_user_skills():
    """获取用户所有技能的启用状态"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401

    username = session['username']
    all_skills = skill_registry.list_skills()

    # 获取用户设置的技能状态
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT skill_name, enabled FROM user_skills WHERE username = %s",
                (username,)
            )
            user_settings = {row['skill_name']: row['enabled'] for row in cursor.fetchall()}

    # 组合所有技能信息
    skills = []
    for skill_name in all_skills:
        skill = skill_registry.get_skill(skill_name)
        if skill:
            enabled = user_settings.get(skill_name, 1)
            skills.append({
                'name': skill.name,
                'description': skill.description,
                'enabled': bool(enabled)
            })

    return jsonify({
        'skills': skills,
        'count': len(skills)
    })

@app.route('/api/user/skills/<skill_name>', methods=['PUT'])
def update_user_skill(skill_name):
    """更新用户指定技能的启用状态"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401

    username = session['username']
    all_skills = skill_registry.list_skills()

    if skill_name not in all_skills:
        return jsonify({'error': '技能不存在'}), 404

    try:
        data = request.json
        enabled = data.get('enabled', True)

        if not isinstance(enabled, bool):
            enabled = bool(enabled)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_skills (username, skill_name, enabled) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE enabled = %s, updated_at = CURRENT_TIMESTAMP",
                    (username, skill_name, int(enabled), int(enabled))
                )
                conn.commit()

        return jsonify({
            'success': True,
            'skill_name': skill_name,
            'enabled': enabled
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_user_enabled_skills(username):
    """获取用户所有启用的技能"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT skill_name FROM user_skills WHERE username = %s AND enabled = 1",
                (username,)
            )
            enabled_skills = {row['skill_name'] for row in cursor.fetchall()}

    all_skills = skill_registry.list_skills()
    return [s for s in all_skills if s in enabled_skills or s not in set(enabled_skills)]

def get_enabled_skills_for_user(username):
    """获取用户启用的技能列表（未设置的技能默认启用）"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT skill_name, enabled FROM user_skills WHERE username = %s",
                (username,)
            )
            user_settings = {row['skill_name']: row['enabled'] for row in cursor.fetchall()}

    all_skills = skill_registry.list_skills()
    enabled_skills = []
    for skill_name in all_skills:
        if skill_name in user_settings:
            if user_settings[skill_name]:
                enabled_skills.append(skill_name)
        else:
            enabled_skills.append(skill_name)
    return enabled_skills

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # 确保模板目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # 初始化数据库表
    try:
        init_database()
    except Exception as e:
        print(f"⚠️  数据库初始化失败: {e}")
        print("   请确保 MySQL 已启动并配置正确的连接信息")
    
    print("\n" + "="*50)
    print("🚀 AI Chat Platform Starting...")
    print("="*50)
    
    # 检查 API Key 配置
    if OPENAI_API_KEY:
        print("✅ API Key: 已配置")
        print(f"🔗 API URL: {OPENAI_BASE_URL}")
    else:
        print("⚠️  API Key: 未配置 (请在 .env 文件中设置 OPENAI_API_KEY)")
    
    # 显示已加载的技能
    print(f"🎯 已加载技能: {len(skill_registry)} 个")
    for skill_name in skill_registry.list_skills():
        skill = skill_registry.get_skill(skill_name)
        print(f"   - {skill_name}: {skill.description[:50]}...")
    
    print(f"📝 访问地址: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
