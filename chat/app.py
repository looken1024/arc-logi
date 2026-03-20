from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for, send_file, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta
import openai
from typing import Generator
import secrets
import io
import requests
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
import pymysql
import uuid
import subprocess
import threading
import smtplib
import redis
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from contextlib import contextmanager

# 导入 skills 模块
from skills import register_all_skills

# 导入调度器模块
from scheduler import scheduler

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_NAME'] = 'chat_session'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

# Skills 目录配置
SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skills')
USER_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_skills')

# 确保用户skills目录存在
os.makedirs(USER_SKILLS_DIR, exist_ok=True)

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
            
            # 创建工作流表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    username VARCHAR(50) NOT NULL,
                    status ENUM('draft', 'active', 'paused', 'archived') DEFAULT 'draft',
                    definition JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建工作流节点表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_nodes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    workflow_id INT NOT NULL,
                    node_id VARCHAR(50) NOT NULL,
                    node_type ENUM('start', 'end', 'llm', 'script', 'condition', 'input', 'output', 'delay', 'base64', 'json', 'sql', 'http') NOT NULL,
                    name VARCHAR(100),
                    config JSON,
                    position_x INT DEFAULT 0,
                    position_y INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_workflow_id (workflow_id),
                    INDEX idx_node_type (node_type),
                    UNIQUE KEY uk_workflow_node (workflow_id, node_id),
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建工作流边表（节点连接关系）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_edges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    workflow_id INT NOT NULL,
                    source_node_id VARCHAR(50) NOT NULL,
                    target_node_id VARCHAR(50) NOT NULL,
                    `condition` TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_workflow_id (workflow_id),
                    INDEX idx_source_target (source_node_id, target_node_id),
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建工作流执行表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    workflow_id INT NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    execution_id VARCHAR(64) NOT NULL,
                    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
                    input_data JSON,
                    output_data JSON,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_workflow_id (workflow_id),
                    INDEX idx_username (username),
                    INDEX idx_execution_id (execution_id),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建工作流节点执行表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_node_executions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    execution_id INT NOT NULL,
                    node_id VARCHAR(50) NOT NULL,
                    node_type VARCHAR(50) NOT NULL,
                    status ENUM('pending', 'running', 'completed', 'failed', 'skipped') DEFAULT 'pending',
                    input_data JSON,
                    output_data JSON,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_execution_id (execution_id),
                    INDEX idx_node_id (node_id),
                    INDEX idx_status (status),
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建定时任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    username VARCHAR(50) NOT NULL,
                    cron VARCHAR(50) NOT NULL,
                    preset VARCHAR(50),
                    command TEXT NOT NULL,
                    status ENUM('active', 'paused') DEFAULT 'active',
                    last_run_at DATETIME,
                    next_run_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_username_created (username, created_at),
                    INDEX idx_status (status),
                    INDEX idx_next_run_at (next_run_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建定时任务执行表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedule_executions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    schedule_id INT NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    execution_id VARCHAR(64) NOT NULL,
                    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
                    output TEXT,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_schedule_id (schedule_id),
                    INDEX idx_username (username),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建异步任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS async_tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    task_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    command TEXT NOT NULL,
                    status ENUM('pending', 'scheduled', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
                    output TEXT,
                    error_message TEXT,
                    execution_id VARCHAR(64) NOT NULL,
                    scheduled_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    INDEX idx_username (username),
                    INDEX idx_username_created (username, created_at),
                    INDEX idx_status (status),
                    INDEX idx_execution_id (execution_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建提示词表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    description TEXT,
                    username VARCHAR(50) NOT NULL,
                    tags VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_name (name),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建Agent表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    system_prompt TEXT,
                    prompt_id INT,
                    model VARCHAR(50) DEFAULT 'gpt-4',
                    temperature FLOAT DEFAULT 0.7,
                    max_tokens INT DEFAULT 2000,
                    username VARCHAR(50) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_name (name),
                    INDEX idx_prompt_id (prompt_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建Agent技能关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_agent_skill (agent_id, skill_name),
                    INDEX idx_agent_id (agent_id),
                    INDEX idx_skill_name (skill_name),
                    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建工作流搜索历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_search_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    search_keyword VARCHAR(200) NOT NULL,
                    search_type VARCHAR(20) DEFAULT 'workflow',
                    search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_search_time (search_time),
                    INDEX idx_keyword (search_keyword)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建热门搜索表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS popular_searches (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    keyword VARCHAR(200) NOT NULL,
                    search_type VARCHAR(20) DEFAULT 'workflow',
                    search_count INT DEFAULT 1,
                    last_searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_keyword_type (keyword, search_type),
                    INDEX idx_search_count (search_count),
                    INDEX idx_last_searched (last_searched_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 为 workflows 表添加 username 索引（如果不存在）
            try:
                cursor.execute("""
                    SHOW INDEX FROM workflows WHERE Key_name = 'idx_username'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE workflows ADD INDEX idx_username (username)
                    """)
                    print("✅ 已添加 username 索引到 workflows 表")
            except Exception as e:
                print(f"添加 username 索引失败: {e}")

            # 为 async_tasks 表添加 scheduled_at 列（如果不存在）
            try:
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'async_tasks' 
                    AND COLUMN_NAME = 'scheduled_at'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE async_tasks 
                        ADD COLUMN scheduled_at DATETIME NULL DEFAULT NULL
                    """)
                    print("✅ 已添加 scheduled_at 列到 async_tasks 表")
            except Exception as e:
                print(f"添加 scheduled_at 列失败: {e}")
            
            # 为 async_tasks 表添加 scheduled 状态到 status 枚举（如果不存在）
            try:
                cursor.execute("""
                    SELECT COLUMN_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'async_tasks' 
                    AND COLUMN_NAME = 'status'
                """)
                row = cursor.fetchone()
                if row and 'scheduled' not in row['COLUMN_TYPE']:
                    cursor.execute("""
                        ALTER TABLE async_tasks 
                        MODIFY COLUMN status ENUM('pending', 'running', 'completed', 'failed', 'scheduled') DEFAULT 'pending'
                    """)
                    print("✅ 已添加 scheduled 状态到 async_tasks 表")
            except Exception as e:
                print(f"修改 status 枚举失败: {e}")
            
            # 创建知识库表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    username VARCHAR(50) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建知识条目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    knowledge_base_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    type ENUM('text', 'qa', 'concept', 'procedure') DEFAULT 'text',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_knowledge_base_id (knowledge_base_id),
                    INDEX idx_type (type),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建知识关系表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relation (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    knowledge_base_id INT NOT NULL,
                    source_item_id INT DEFAULT NULL,
                    target_item_id INT NOT NULL,
                    relation_type ENUM('related', 'parent', 'child', 'similar', 'tag') DEFAULT 'related',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_knowledge_base_id (knowledge_base_id),
                    INDEX idx_source_item_id (source_item_id),
                    INDEX idx_target_item_id (target_item_id),
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            conn.commit()
            print("✅ 数据库表初始化完成")

# 初始化技能注册表
skill_registry = register_all_skills()

def execute_async_task(task_id, execution_id, command):
    """执行异步任务命令"""
    # 先更新状态为运行中
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE async_tasks SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE execution_id = %s",
                    (execution_id,)
                )
                conn.commit()
    except Exception as e:
        print(f"更新异步任务状态为运行中失败: {e}")
    
    # 调用调度器的异步任务执行函数（支持实时输出）
    try:
        scheduler.execute_async_command(task_id, execution_id, command)
    except Exception as e:
        print(f"执行异步任务失败: {e}")


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

@app.route('/color')
def color_tool():
    """颜色选择器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('color.html')

@app.route('/datetime')
def datetime_tool():
    """时间转换器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('datetime.html')

@app.route('/image')
def image_tool():
    """图片转换工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('image.html')

@app.route('/pdf')
def pdf_tool():
    """PDF 阅读器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('pdf.html')

@app.route('/video')
def video_tool():
    """视频转换工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('video.html')

@app.route('/certificate')
def certificate_tool():
    """奖状生成器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('certificate.html')

@app.route('/email')
def email_tool():
    """邮件发送页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('email.html')

@app.route('/hex')
def hex_tool():
    """进制转换器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('hex.html')

@app.route('/api/email/send', methods=['POST'])
def send_email():
    """发送邮件API"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            to_email = request.form.get('to', '').strip()
            subject = request.form.get('subject', '').strip()
            content = request.form.get('content', '').strip()
            files = request.files.getlist('attachments')
        else:
            data = request.get_json()
            to_email = data.get('to', '').strip()
            subject = data.get('subject', '').strip()
            content = data.get('content', '').strip()
            files = []
        
        if not to_email or not subject or not content:
            return jsonify({'success': False, 'error': '参数不完整'})
        
        smtp_host = os.getenv('SMTP_HOST', 'smtp.qq.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        smtp_from = os.getenv('SMTP_FROM', smtp_user)
        
        if not smtp_user or not smtp_password:
            return jsonify({'success': False, 'error': '邮件服务器未配置'})
        
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        for file in files:
            if file.filename:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={file.filename}')
                msg.attach(part)
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return jsonify({'success': True, 'message': '邮件发送成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/regex')
def regex_tool():
    """正则表达式工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('regex.html')

@app.route('/whiteboard')
def whiteboard_tool():
    """白板工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('whiteboard.html')

@app.route('/linux')
def linux_tool():
    """Linux 命令工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('linux.html')

@app.route('/weather')
def weather_tool():
    """天气查询工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('weather.html')

@app.route('/markdown')
def markdown_tool():
    """Markdown 格式转换工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('markdown.html')

@app.route('/api/weather/query', methods=['POST'])
def query_weather():
    """查询天气API"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    data = request.get_json()
    city = data.get('city', '').strip()
    
    if not city:
        return jsonify({'success': False, 'error': '请输入城市名称'})
    
    try:
        import requests
        api_key = 'eb4e86c2b456401cbae17a8d9eab0712'
        
        geocode_url = f'https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}'
        geocode_response = requests.get(geocode_url, timeout=10)
        geocode_data = geocode_response.json()
        
        if geocode_data.get('code') != '200':
            return jsonify({'success': False, 'error': '城市未找到'})
        
        location = geocode_data['location'][0]
        location_id = location['id']
        city_name = location['name']
        city_adm = location.get('adm2', location.get('adm1', ''))
        
        weather_url = f'https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}'
        weather_response = requests.get(weather_url, timeout=10)
        weather_data = weather_response.json()
        
        if weather_data.get('code') != '200':
            return jsonify({'success': False, 'error': '天气数据获取失败'})
        
        now = weather_data['now']
        
        return jsonify({
            'success': True,
            'city': city_name,
            'province': city_adm,
            'temp': now['temp'],
            'text': now['text'],
            'windDir': now['windDir'],
            'windScale': now['windScale'],
            'humidity': now['humidity'],
            'feelsLike': now['feelsLike'],
            'vis': now['vis'],
            'pressure': now['pressure'],
            'updateTime': weather_data.get('updateTime', '')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'查询失败: {str(e)}'})

@app.route('/shorturl')
def shorturl_tool():
    """短链接工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('shorturl.html')

@app.route('/api/shorturl/create', methods=['POST'])
def create_shorturl():
    """创建短链接"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    data = request.get_json()
    original_url = data.get('original_url', '').strip()
    custom_code = data.get('custom_code', '').strip()
    
    if not original_url:
        return jsonify({'success': False, 'error': '请输入原始URL'})
    
    from urllib.parse import urlparse
    try:
        result = urlparse(original_url)
        if not all([result.scheme, result.netloc]):
            return jsonify({'success': False, 'error': '无效的URL格式'})
    except:
        return jsonify({'success': False, 'error': '无效的URL格式'})
    
    import random
    import string
    import re
    
    def generate_code(length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def validate_code(code):
        return bool(re.match(r'^[a-zA-Z0-9]{1,6}$', code))
    
    if custom_code:
        if not validate_code(custom_code):
            return jsonify({'success': False, 'error': '自定义短码只能使用1-6位字母数字'})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if custom_code:
                    cursor.execute("SELECT id FROM short_urls WHERE short_code = %s", (custom_code,))
                    if cursor.fetchone():
                        return jsonify({'success': False, 'error': f'短码 {custom_code} 已被占用'})
                else:
                    while True:
                        custom_code = generate_code(6)
                        cursor.execute("SELECT id FROM short_urls WHERE short_code = %s", (custom_code,))
                        if not cursor.fetchone():
                            break
                
                cursor.execute(
                    "INSERT INTO short_urls (original_url, short_code, created_at) VALUES (%s, %s, NOW())",
                    (original_url, custom_code)
                )
                conn.commit()
        
        short_domain = os.getenv('SHORT_URL_DOMAIN', request.host_url.rstrip('/'))
        short_url = f"{short_domain}s/{custom_code}"
        
        return jsonify({
            'success': True,
            'original_url': original_url,
            'short_code': custom_code,
            'short_url': short_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'创建短链接失败: {str(e)}'})

@app.route('/s/<code>')
def redirect_shorturl(code):
    """短链接重定向"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT original_url FROM short_urls WHERE short_code = %s", (code,))
                result = cursor.fetchone()
        
        if result:
            return redirect(result['original_url'])
        else:
            return "短链接不存在", 404
    except:
        return "短链接不存在", 404

LINUX_COMMAND_PROMPT = """你是一个Linux命令专家，擅长介绍各种Linux命令的用法、选项和示例。

用户会输入一个Linux命令名称或相关关键词，你需要提供该命令的详细信息，包括：
1. 命令名称和基本作用
2. 语法格式
3. 常用选项和参数说明
4. 实际使用示例（2-3个）
5. 注意事项和常见用法

请用Markdown格式输出，内容要准确、简洁、实用。如果用户输入的不是有效的命令名称，请提供相关的建议。"""

@app.route('/api/linux/query', methods=['POST'])
def linux_query():
    """查询Linux命令"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'error': '请输入命令名称'})
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=60.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": LINUX_COMMAND_PROMPT},
                {"role": "user", "content": f"请介绍 Linux 命令「{command}」的用法"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

GIT_COMMAND_PROMPT = """你是一个Git版本控制专家，擅长介绍各种Git命令的用法、选项和示例。

用户会输入一个Git命令名称或相关关键词，你需要提供该命令的详细信息，包括：
1. 命令名称和基本作用
2. 语法格式
3. 常用选项和参数说明
4. 实际使用示例（2-3个）
5. 注意事项和常见用法

如果用户输入的不是有效的Git命令，请提供相关的建议。

最好以表格的形式提供选项说明。"""

@app.route('/git')
def git_tool():
    """Git 使用工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('git.html')

@app.route('/api/git/query', methods=['POST'])
def git_query():
    """查询Git命令"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'error': '请输入命令名称'})
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=60.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": GIT_COMMAND_PROMPT},
                {"role": "user", "content": f"请介绍 Git 命令「{command}」的用法"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stock')
def stock_tool():
    """股票行情工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('stock.html')

@app.route('/api/stock/quote')
def stock_quote():
    """获取股票实时行情"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    code = request.args.get('code', '').strip().upper()
    if not code:
        return jsonify({'success': False, 'error': '请输入股票代码'})
    
    try:
        import httpx
        
        # 判断股票市场
        if code.startswith('6') or code.startswith('688'):
            # 上海主板/科创板
            symbol = f'sh{code}'
        elif code.startswith('00') or code.startswith('30'):
            # 深圳主板/创业板
            symbol = f'sz{code}'
        elif code.startswith('8') or code.startswith('4'):
            # 北京交所
            symbol = f'bj{code}'
        else:
            symbol = code
        
        # 使用新浪财经API获取实时行情
        url = f'https://hq.sinajs.cn/list={symbol}'
        headers = {
            'Referer': 'https://finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.encoding = 'gbk'
        content = response.text
        
        if not content or 'var hq_str_' not in content:
            return jsonify({'success': False, 'error': '股票代码不存在或已退市'})
        
        # 解析返回数据
        data_line = content.split('=')[1].strip('";\n')
        if not data_line:
            return jsonify({'success': False, 'error': '无法获取股票数据'})
        
        fields = data_line.split(',')
        
        if len(fields) < 32:
            return jsonify({'success': False, 'error': '数据格式错误'})
        
        name = fields[0]
        open_price = fields[1]
        pre_close = fields[2]
        price = fields[3]
        high = fields[4]
        low = fields[5]
        volume = fields[8]
        amount = fields[9]
        
        # 计算涨跌和涨跌幅
        try:
            pre_close_float = float(pre_close)
            price_float = float(price)
            change = round(price_float - pre_close_float, 2)
            change_percent = round((change / pre_close_float) * 100, 2) if pre_close_float != 0 else 0
        except:
            change = 0
            change_percent = 0
        
        # 判断市场
        if code.startswith('6') or code.startswith('688'):
            market = '上海证券交易所'
        elif code.startswith('00') or code.startswith('30'):
            market = '深圳证券交易所'
        elif code.startswith('8') or code.startswith('4'):
            market = '北京证券交易所'
        else:
            market = '未知市场'
        
        # 格式化成交量
        try:
            vol = float(volume)
            if vol >= 100000000:
                volume_str = f'{vol/100000000:.2f}亿'
            elif vol >= 10000:
                volume_str = f'{vol/10000:.2f}万'
            else:
                volume_str = str(vol)
        except:
            volume_str = volume
        
        # 格式化成交额
        try:
            amt = float(amount)
            if amt >= 100000000:
                amount_str = f'{amt/100000000:.2f}亿'
            elif amt >= 10000:
                amount_str = f'{amt/10000:.2f}万'
            else:
                amount_str = str(amount)
        except:
            amount_str = amount
        
        # 计算涨跌停
        try:
            limit_up = round(pre_close_float * 1.10, 2) if pre_close_float != 0 else 0
            limit_down = round(pre_close_float * 0.90, 2) if pre_close_float != 0 else 0
        except:
            limit_up = 0
            limit_down = 0
        
        return jsonify({
            'success': True,
            'data': {
                'code': code,
                'name': name,
                'market': market,
                'price': price,
                'change': f'{change:+.2f}',
                'changePercent': f'{change_percent:+.2f}%',
                'open': open_price,
                'preClose': pre_close,
                'high': high,
                'low': low,
                'volume': volume_str,
                'amount': amount_str,
                'limitUp': f'{limit_up:.2f}' if limit_up else '-',
                'limitDown': f'{limit_down:.2f}' if limit_down else '-',
                'pe': '-'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取数据失败: {str(e)}'})

@app.route('/api/stock/history')
def stock_history():
    """获取股票历史行情"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'})
    
    code = request.args.get('code', '').strip().upper()
    trend_type = request.args.get('type', 'day')
    
    if not code:
        return jsonify({'success': False, 'error': '请输入股票代码'})
    
    try:
        import httpx
        
        # 判断股票市场
        if code.startswith('6') or code.startswith('688'):
            symbol = f'sh{code}'
        elif code.startswith('00') or code.startswith('30'):
            symbol = f'sz{code}'
        elif code.startswith('8') or code.startswith('4'):
            symbol = f'bj{code}'
        else:
            symbol = code
        
        # 使用网易财经API获取历史数据
        if trend_type == 'day':
            url = f'https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=5'
        elif trend_type == 'week':
            url = f'https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=Weekly&ma=5'
        else:  # month
            url = f'https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData?symbol={symbol}&scale=Monthly&ma=5'
        
        headers = {
            'Referer': 'https://finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.encoding = 'gbk'
        content = response.text
        
        # 解析JSON数据
        import re
        json_match = re.search(r'\[.*\]', content)
        if not json_match:
            return jsonify({'success': False, 'error': '暂无历史数据'})
        
        import json
        data = json.loads(json_match.group())
        
        if not data:
            return jsonify({'success': False, 'error': '暂无历史数据'})
        
        history = []
        for i, item in enumerate(data):
            try:
                close = float(item.get('close', 0))
                if i > 0:
                    prev_close = float(data[i-1].get('close', 0))
                    if prev_close > 0:
                        change = round((close - prev_close) / prev_close * 100, 2)
                    else:
                        change = 0
                else:
                    change = 0
                history.append({
                    'date': item.get('day', ''),
                    'open': item.get('open', ''),
                    'high': item.get('high', ''),
                    'low': item.get('low', ''),
                    'close': item.get('close', ''),
                    'volume': item.get('volume', ''),
                    'change': str(change)
                })
            except:
                continue
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取历史数据失败: {str(e)}'})

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff', 'ico'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/api/image/convert', methods=['POST'])
def image_convert():
    """图片格式转换"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})
    
    file = request.files['file']
    target_format = request.form.get('format', 'PNG').upper()
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})
    
    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({'success': False, 'error': '不支持的图片格式'})
    
    try:
        image = Image.open(file)
        if image.mode == 'RGBA' and target_format in ['JPEG', 'JPG']:
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB' and target_format in ['JPEG', 'JPG']:
            image = image.convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format=target_format)
        output.seek(0)
        
        return send_file(
            output,
            mimetype=f'image/{target_format.lower()}',
            as_attachment=True,
            download_name=f'converted.{target_format.lower()}'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/image/to-pdf', methods=['POST'])
def image_to_pdf():
    """图片转PDF"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})
    
    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({'success': False, 'error': '不支持的图片格式'})
    
    try:
        image = Image.open(file)
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        pdf_output = io.BytesIO()
        image.save(pdf_output, 'PDF', resolution=100.0)
        pdf_output.seek(0)
        
        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='converted.pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/pdf/to-image', methods=['POST'])
def pdf_to_image():
    """PDF转图片"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})
    
    if not allowed_file(file.filename, ALLOWED_PDF_EXTENSIONS):
        return jsonify({'success': False, 'error': '请上传PDF文件'})
    
    try:
        import fitz
        pdf_data = file.read()
        pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        if pdf_doc.page_count == 0:
            return jsonify({'success': False, 'error': 'PDF文件为空'})
        
        page = pdf_doc[0]
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        
        return send_file(
            io.BytesIO(img_data),
            mimetype='image/png',
            as_attachment=True,
            download_name='page_1.png'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mp3'}

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'webm', 'mp4', 'flac', 'aac', 'opus'}

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

@app.route('/api/video/convert', methods=['POST'])
def video_convert():
    """视频格式转换"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})
    
    file = request.files['file']
    target_format = request.form.get('format', 'MP4').upper()
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})
    
    if not allowed_video_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的视频格式'})
    
    try:
        import uuid
        import shutil
        
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        input_ext = file.filename.rsplit('.', 1)[1].lower()
        input_filename = f"{uuid.uuid4()}.{input_ext}"
        input_path = os.path.join(temp_dir, input_filename)
        output_filename = f"{uuid.uuid4()}.{target_format.lower()}"
        output_path = os.path.join(temp_dir, output_filename)
        
        file.save(input_path)
        
        if target_format == 'MP3':
            cmd = ['ffmpeg', '-i', input_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', output_path]
        else:
            cmd = ['ffmpeg', '-i', input_path, '-c:v', 'libx264', '-c:a', 'aac', '-y', output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        os.remove(input_path)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else '转换失败'
            if 'ffmpeg' in error_msg.lower() or 'not found' in error_msg.lower():
                return jsonify({'success': False, 'error': '服务器未安装 ffmpeg，请联系管理员安装'})
            return jsonify({'success': False, 'error': f'转换失败: {error_msg}'})
        
        with open(output_path, 'rb') as f:
            output_data = f.read()
        
        os.remove(output_path)
        
        mime_types = {
            'MP4': 'video/mp4',
            'AVI': 'video/x-msvideo',
            'MKV': 'video/x-matroska',
            'MOV': 'video/quicktime',
            'WEBM': 'video/webm',
            'MP3': 'audio/mpeg'
        }
        
        original_name = file.filename.rsplit('.', 1)[0]
        
        return send_file(
            io.BytesIO(output_data),
            mimetype=mime_types.get(target_format, 'application/octet-stream'),
            as_attachment=True,
            download_name=f'{original_name}.{target_format.lower()}'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/voice/recognize', methods=['POST'])
def voice_recognize():
    """语音转文字"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '请选择文件'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '请选择文件'})
    
    if not allowed_audio_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的音频格式'})
    
    try:
        if not OPENAI_API_KEY:
            return jsonify({'success': False, 'error': '未配置 OpenAI API Key'})
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        import uuid
        input_ext = file.filename.rsplit('.', 1)[1].lower()
        input_filename = f"{uuid.uuid4()}.{input_ext}"
        input_path = os.path.join(temp_dir, input_filename)
        file.save(input_path)
        
        with open(input_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh"
            )
        
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'text': transcript.text
        })
        
    except openai.OpenAIError as e:
        return jsonify({'success': False, 'error': f'语音识别失败: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

MICRO_HEADLINE_SYSTEM_PROMPT = """你是一位资深的微头条文案专家，擅长创作吸引眼球的爆款微头条内容。

请根据用户提供的关键词或主题，生成一篇优质的微头条文案。

要求：
1. 开头要有吸引力，能够引发用户好奇或共鸣
2. 内容简洁有力，控制在200-500字左右
3. 语言风格接地气口语化，适合手机阅读
4. 可以适当添加emoji表情增加趣味性
5. 结尾可以添加互动话题，引导用户评论
6. 段落分明，每段不超过3行

请直接输出文案内容，不要添加任何解释或格式符号。"""

RECIPE_SYSTEM_PROMPT = """你是一位专业的中餐厨师，擅长创作各种美味菜品的详细制作步骤。

用户会提供一道菜名，你需要为这道菜生成详细的制作步骤。
请严格按照以下表格格式输出：

| 步骤 | 操作内容 | 注意事项 |
|------|----------|----------|
| 1    | 具体操作 | 需要注意的细节 |
| 2    | 具体操作 | 需要注意的细节 |
| ...  | ...      | ...      |

要求：
1. 步骤要详细清晰，每一步都要包含具体操作和注意事项
2. 包含所需食材和调料（如果有）
3. 考虑烹饪时间、火候、食材处理等关键细节
4. 如果是家常菜，要提供简单易懂的步骤
5. 如果是复杂菜品，可以适当增加步骤数量
6. 输出必须只包含表格，不要有任何其他文字解释"""

@app.route('/recipes')
def recipe_tool():
    """菜谱生成器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('recipes.html')

@app.route('/api/recipes/generate', methods=['POST'])
def recipe_generate():
    """生成菜谱制作步骤"""
    data = request.get_json()
    dish_name = data.get('dish_name', '').strip()
    
    if not dish_name:
        return jsonify({'success': False, 'error': '请输入菜名'})
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=120.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": RECIPE_SYSTEM_PROMPT},
                {"role": "user", "content": f"请生成菜名「{dish_name}」的详细制作步骤，以表格形式呈现"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/weibo')
def weibo_tool():
    """微头条文案工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('weibo.html')

@app.route('/api/weibo/generate', methods=['POST'])
def weibo_generate():
    """生成微头条文案"""
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'success': False, 'error': '请输入关键词或主题'})
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=60.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": MICRO_HEADLINE_SYSTEM_PROMPT},
                {"role": "user", "content": f"请为以下主题生成微头条文案：{keyword}"}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

WECHAT_SYSTEM_PROMPT = """你是一位专业的微信公众号运营专家，擅长创作高质量的公众号文章。

用户会提供以下信息：
- 细分领域：如 AI技术、职场干货、情感心理、生活技巧等
- 热门趋势：当前热门话题或关键词

请按照以下工作流程生成完整的微信公众号文章：

## 1. 选题分析
根据用户提供的领域和趋势，选择一个具体且有吸引力的文章主题。

## 2. 文章大纲
设计一个清晰的文章结构，包括：
- 开头钩子：吸引读者注意力的开场
- 主体内容：3-5个主要论点，每个论点需要有案例或数据支撑
- 结尾总结：给读者留下深刻印象的结尾

## 3. 标题和摘要
生成3个备选标题和一段吸引人的摘要。

## 4. 完整文章
撰写完整的文章内容，要求：
- 语言风格专业但不晦涩，亲切但不随意
- 段落长度适中，适合手机阅读
- 适当使用表情符号增加趣味性
- 字数控制在1500-3000字之间
- 文章内容要原创、有价值、有深度

输出格式使用 Markdown，包含标题、摘要、正文内容。"""

@app.route('/wechat')
def wechat_tool():
    """微信公众号内容生成工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('wechat.html')

@app.route('/api/wechat/generate', methods=['POST'])
def wechat_generate():
    """生成微信公众号文章"""
    data = request.get_json()
    niche = data.get('niche', '').strip()
    trends = data.get('trends', '').strip()
    
    if not niche:
        return jsonify({'success': False, 'error': '请输入细分领域'})
    
    if not trends:
        return jsonify({'success': False, 'error': '请输入热门趋势'})
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=180.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": WECHAT_SYSTEM_PROMPT},
                {"role": "user", "content": f"请为以下领域和趋势生成微信公众号文章：\n\n细分领域：{niche}\n热门趋势：{trends}"}
            ],
            temperature=0.8,
            max_tokens=4000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

NAMING_SYSTEM_PROMPT = """你是一位专业的姓名学大师，擅长根据八字五行、生肖、星座等为新生儿起名。

用户会提供以下信息：
- 性别：男孩或女孩
- 出生日期：年-月-日
- 出生时辰（如有）：子时、丑时等
- 姓氏（如有）：姓什么

请根据以上信息生成吉祥的名字，要求：
1. 提供3-5个精选名字，每个名字都要有详细的起名原因分析
2. 分析八字五行，看看宝宝缺什么，然后在名字中补充
3. 考虑名字的音韵美感，读起来朗朗上口
4. 名字要有美好的寓意和象征
5. 名字要容易被接受，寓意积极向上

输出格式请使用Markdown，方便前端渲染显示。"""

@app.route('/naming')
def naming_tool():
    """起名神器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('naming.html')

@app.route('/api/naming/generate', methods=['POST'])
def naming_generate():
    """生成名字"""
    data = request.get_json()
    gender = data.get('gender', '').strip()
    birth_date = data.get('birth_date', '').strip()
    birth_time = data.get('birth_time', '').strip()
    surname = data.get('surname', '').strip()
    
    if not birth_date:
        return jsonify({'success': False, 'error': '请选择出生日期'})
    
    user_content = f"请为"
    if surname:
        user_content += f"姓{surname}的"
    user_content += f"宝宝起名，性别：{gender}，出生日期：{birth_date}"
    if birth_time:
        user_content += f"，出生时辰：{birth_time}"
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=120.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": NAMING_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tools')
def tools():
    """工具列表页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('tools.html')

@app.route('/api/http-request', methods=['POST'])
def http_request_proxy():
    """HTTP请求代理API，解决前端CORS问题"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json()
    url = data.get('url', '')
    method = data.get('method', 'GET')
    headers = data.get('headers', {})
    body = data.get('body', None)
    
    if not url:
        return jsonify({'success': False, 'error': 'URL不能为空'}), 400
    
    try:
        request_kwargs = {
            'url': url,
            'method': method,
            'headers': headers,
            'timeout': 30
        }
        
        if body and method in ['POST', 'PUT', 'PATCH']:
            request_kwargs['data'] = body
            
        response = requests.request(**request_kwargs)
        
        content_type = response.headers.get('Content-Type', '')
        encoding = 'utf-8'
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip()
            encoding = charset
        
        try:
            data = response.content.decode(encoding)
        except:
            for enc in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
                try:
                    data = response.content.decode(enc)
                    break
                except:
                    continue
            else:
                data = response.content.decode('utf-8', errors='replace')
        
        return jsonify({
            'success': True,
            'status': response.status_code,
            'statusText': response.reason,
            'headers': dict(response.headers),
            'data': data
        })
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': '请求超时'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500

CLASSIC_SYSTEM_PROMPT = """你是一个中国传统文化专家，擅长解读经典古籍。你的任务是用通俗易懂的语言解读三字经、千字文等传统启蒙经典，帮助用户理解其含义、教育思想和历史价值。

输出格式请使用Markdown，方便前端渲染显示。"""

@app.route('/sanzijing')
def sanzijing_tool():
    """三字经页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('sanzijing.html')

@app.route('/qianziwen')
def qianziwen_tool():
    """千字文页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('qianziwen.html')

@app.route('/api/classic/analyze', methods=['POST'])
def classic_analyze():
    """经典解读"""
    data = request.get_json()
    classic = data.get('classic', '')
    user_content = data.get('user_content', '')
    
    classic_name = '三字经' if classic == 'sanzijing' else '千字文'
    
    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=120.0,
            max_retries=2
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": CLASSIC_SYSTEM_PROMPT},
                {"role": "user", "content": f"关于{classic_name}：{user_content}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/skills')
def skills_page():
    """Skills 管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('skills.html')

@app.route('/base64')
def base64_tool():
    """Base64 工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('base64.html')

@app.route('/diff')
def diff_tool():
    """文本差异对比工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('diff.html')

@app.route('/json')
def json_tool():
    """JSON 工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('json.html')

@app.route('/sql')
def sql_tool():
    """SQL 工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('sql.html')

@app.route('/http')
def http_tool():
    """HTTP 请求工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('http.html')

@app.route('/schedules')
def schedules():
    """定时任务管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('schedules.html')

@app.route('/async_tasks')
def async_tasks():
    """异步任务管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT theme FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            user_theme = result.get('theme', 'dark') if result else 'dark'
    
    return render_template('async_tasks.html', user_theme=user_theme)

@app.route('/workflows')
def workflows():
    """工作流管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('workflows.html')

@app.route('/prompts')
def prompts_page():
    """提示词管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('prompts.html')

@app.route('/agents')
def agents_page():
    """Agent管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('agents.html')

@app.route('/voice')
def voice_page():
    """语音转文字页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('voice.html')

@app.route('/workflows/editor/<int:workflow_id>')
def workflow_editor(workflow_id):
    """工作流编辑器页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # 验证工作流存在且属于当前用户
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, status, username 
                FROM workflows 
                WHERE id = %s AND username = %s
            """, (workflow_id, session['username']))
            workflow = cursor.fetchone()
    
    if not workflow:
        return "工作流不存在或无权访问", 404
    
    return render_template('workflow_editor.html', workflow_id=workflow_id)

@app.route('/knowledge')
def knowledge_page():
    """知识库管理页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('knowledge.html')

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
        
        if theme not in ['dark', 'light', 'blue', 'green', 'purple', 'red', 'orange', 'pink', 'cyan', 'indigo']:
            return jsonify({'error': '无效的主题'}), 400
        
        username = session['username']
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET theme = %s WHERE username = %s", (theme, username))
                conn.commit()
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """获取用户个人信息"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_profile WHERE username = %s", (username,))
            profile = cursor.fetchone()
            
            cursor.execute("SELECT * FROM user_preferences WHERE username = %s", (username,))
            preferences = cursor.fetchone()
    
    if not profile:
        profile = {
            'username': username,
            'nickname': '',
            'real_name': '',
            'gender': 'unknown',
            'age': None,
            'occupation': '',
            'bio': '',
            'preferences': {}
        }
    
    if not preferences:
        preferences = {
            'username': username,
            'greeting_enabled': True,
            'use_nickname': True,
            'remember_context': True,
            'personalized_responses': True,
            'ai_personality': 'friendly'
        }
    
    return jsonify({
        'profile': profile,
        'preferences': preferences
    })

def get_user_info_for_context(username):
    """获取用户信息，用于注入到对话context中"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM user_profile WHERE username = %s", (username,))
            profile = cursor.fetchone()
            
            cursor.execute("SELECT * FROM user_preferences WHERE username = %s", (username,))
            preferences = cursor.fetchone()
    
    user_info_parts = []
    
    if profile:
        nickname = profile.get('nickname', '').strip()
        real_name = profile.get('real_name', '').strip()
        gender = profile.get('gender', 'unknown')
        age = profile.get('age')
        occupation = profile.get('occupation', '').strip()
        bio = profile.get('bio', '').strip()
        
        if nickname:
            user_info_parts.append(f"用户昵称: {nickname}")
        if real_name:
            user_info_parts.append(f"真实姓名: {real_name}")
        if gender and gender != 'unknown':
            gender_map = {'male': '男', 'female': '女'}
            user_info_parts.append(f"性别: {gender_map.get(gender, gender)}")
        if age:
            user_info_parts.append(f"年龄: {age}")
        if occupation:
            user_info_parts.append(f"职业: {occupation}")
        if bio:
            user_info_parts.append(f"个人简介: {bio}")
    
    if preferences:
        personality = preferences.get('ai_personality', 'friendly')
        personalized = preferences.get('personalized_responses', True)
        
        if personality and personality != 'friendly':
            user_info_parts.append(f"期望的AI性格: {personality}")
        if personalized:
            user_info_parts.append("用户偏好: 希望获得个性化回复")
    
    if user_info_parts:
        return "【用户信息】\n" + "\n".join(user_info_parts)
    return None

@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    """更新用户个人信息"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json
        username = session['username']
        
        profile_data = {
            'username': username,
            'nickname': data.get('nickname', ''),
            'real_name': data.get('real_name', ''),
            'gender': data.get('gender', 'unknown'),
            'age': data.get('age'),
            'occupation': data.get('occupation', ''),
            'bio': data.get('bio', ''),
            'preferences': json.dumps(data.get('preferences', {}), ensure_ascii=False)
        }
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_profile (username, nickname, real_name, gender, age, occupation, bio, preferences)
                    VALUES (%(username)s, %(nickname)s, %(real_name)s, %(gender)s, %(age)s, %(occupation)s, %(bio)s, %(preferences)s)
                    ON DUPLICATE KEY UPDATE
                    nickname = VALUES(nickname),
                    real_name = VALUES(real_name),
                    gender = VALUES(gender),
                    age = VALUES(age),
                    occupation = VALUES(occupation),
                    bio = VALUES(bio),
                    preferences = VALUES(preferences)
                """, profile_data)
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/preferences', methods=['PUT'])
def update_user_preferences():
    """更新用户偏好设置"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.json
        username = session['username']
        
        pref_data = {
            'username': username,
            'greeting_enabled': int(data.get('greeting_enabled', True)),
            'use_nickname': int(data.get('use_nickname', True)),
            'remember_context': int(data.get('remember_context', True)),
            'personalized_responses': int(data.get('personalized_responses', True)),
            'ai_personality': data.get('ai_personality', 'friendly')
        }
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_preferences (username, greeting_enabled, use_nickname, remember_context, personalized_responses, ai_personality)
                    VALUES (%(username)s, %(greeting_enabled)s, %(use_nickname)s, %(remember_context)s, %(personalized_responses)s, %(ai_personality)s)
                    ON DUPLICATE KEY UPDATE
                    greeting_enabled = VALUES(greeting_enabled),
                    use_nickname = VALUES(use_nickname),
                    remember_context = VALUES(remember_context),
                    personalized_responses = VALUES(personalized_responses),
                    ai_personality = VALUES(ai_personality)
                """, pref_data)
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

THEME_CSS_VARS = {
    'dark': {
        '--primary-color': '#10a37f',
        '--secondary-color': '#19c37d',
        '--bg-color': '#0f0f0f',
        '--sidebar-bg': '#171717',
        '--message-bg': '#1a1a1a',
        '--user-message-bg': '#2d2d2d',
        '--border-color': '#2d2d2d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#2a2a2a',
        '--input-bg': '#1f1f1f',
        '--scrollbar-bg': '#2d2d2d',
        '--scrollbar-thumb': '#4d4d4d',
        '--card-bg': '#1e1e1e',
        '--bg-card': '#1e1e1e',
        '--bg-light': '#1a1a1a',
        '--bg-hover': '#333'
    },
    'light': {
        '--primary-color': '#10a37f',
        '--secondary-color': '#19c37d',
        '--bg-color': '#f5f5f5',
        '--sidebar-bg': '#ffffff',
        '--message-bg': '#e5e5e5',
        '--user-message-bg': '#d5d5d5',
        '--border-color': '#d0d0d0',
        '--text-color': '#1a1a1a',
        '--text-primary': '#1a1a1a',
        '--text-secondary': '#666666',
        '--hover-bg': '#e5e5e5',
        '--input-bg': '#ffffff',
        '--scrollbar-bg': '#d0d0d0',
        '--scrollbar-thumb': '#a0a0a0',
        '--card-bg': '#ffffff',
        '--bg-card': '#ffffff',
        '--bg-light': '#e5e5e5',
        '--bg-hover': '#f0f0f0'
    },
    'blue': {
        '--primary-color': '#3b82f6',
        '--secondary-color': '#60a5fa',
        '--bg-color': '#0f1419',
        '--sidebar-bg': '#1e293b',
        '--message-bg': '#1e293b',
        '--user-message-bg': '#2d2d2d',
        '--border-color': '#334155',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#334155',
        '--input-bg': '#1e293b',
        '--scrollbar-bg': '#334155',
        '--scrollbar-thumb': '#4d5d75',
        '--card-bg': '#1e293b',
        '--bg-card': '#1e293b',
        '--bg-light': '#1e293b',
        '--bg-hover': '#334155'
    },
    'green': {
        '--primary-color': '#22c55e',
        '--secondary-color': '#4ade80',
        '--bg-color': '#0a0f0a',
        '--sidebar-bg': '#0f1f0f',
        '--message-bg': '#1a2e1a',
        '--user-message-bg': '#2d4d2d',
        '--border-color': '#2d4d2d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#2d4d2d',
        '--input-bg': '#1a2e1a',
        '--scrollbar-bg': '#2d4d2d',
        '--scrollbar-thumb': '#4d6d4d',
        '--card-bg': '#1a2e1a',
        '--bg-card': '#1a2e1a',
        '--bg-light': '#1a2e1a',
        '--bg-hover': '#2d4d2d'
    },
    'purple': {
        '--primary-color': '#a855f7',
        '--secondary-color': '#c084fc',
        '--bg-color': '#0f0a1a',
        '--sidebar-bg': '#1f0f2f',
        '--message-bg': '#2a1a3a',
        '--user-message-bg': '#4d2d6d',
        '--border-color': '#4d2d6d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#4d2d6d',
        '--input-bg': '#2a1a3a',
        '--scrollbar-bg': '#4d2d6d',
        '--scrollbar-thumb': '#6d4d8d',
        '--card-bg': '#2a1a3a',
        '--bg-card': '#2a1a3a',
        '--bg-light': '#2a1a3a',
        '--bg-hover': '#4d2d6d'
    },
    'red': {
        '--primary-color': '#ef4444',
        '--secondary-color': '#f87171',
        '--bg-color': '#1a0a0a',
        '--sidebar-bg': '#2a0f0f',
        '--message-bg': '#3a1a1a',
        '--user-message-bg': '#6d2d2d',
        '--border-color': '#6d2d2d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#6d2d2d',
        '--input-bg': '#3a1a1a',
        '--scrollbar-bg': '#6d2d2d',
        '--scrollbar-thumb': '#8d4d4d',
        '--card-bg': '#3a1a1a',
        '--bg-card': '#3a1a1a',
        '--bg-light': '#3a1a1a',
        '--bg-hover': '#6d2d2d'
    },
    'orange': {
        '--primary-color': '#f97316',
        '--secondary-color': '#fb923c',
        '--bg-color': '#1a0f0a',
        '--sidebar-bg': '#2a1a0f',
        '--message-bg': '#3a2a1a',
        '--user-message-bg': '#6d4d2d',
        '--border-color': '#6d4d2d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#6d4d2d',
        '--input-bg': '#3a2a1a',
        '--scrollbar-bg': '#6d4d2d',
        '--scrollbar-thumb': '#8d6d4d',
        '--card-bg': '#3a2a1a',
        '--bg-card': '#3a2a1a',
        '--bg-light': '#3a2a1a',
        '--bg-hover': '#6d4d2d'
    },
    'pink': {
        '--primary-color': '#ec4899',
        '--secondary-color': '#f472b6',
        '--bg-color': '#1a0a14',
        '--sidebar-bg': '#2a0f1f',
        '--message-bg': '#3a1a2e',
        '--user-message-bg': '#6d2d4d',
        '--border-color': '#6d2d4d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#6d2d4d',
        '--input-bg': '#3a1a2e',
        '--scrollbar-bg': '#6d2d4d',
        '--scrollbar-thumb': '#8d4d6d',
        '--card-bg': '#3a1a2e',
        '--bg-card': '#3a1a2e',
        '--bg-light': '#3a1a2e',
        '--bg-hover': '#6d2d4d'
    },
    'cyan': {
        '--primary-color': '#06b6d4',
        '--secondary-color': '#22d3ee',
        '--bg-color': '#0a1a1a',
        '--sidebar-bg': '#0f2a2a',
        '--message-bg': '#1a3a3a',
        '--user-message-bg': '#2d6d6d',
        '--border-color': '#2d6d6d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#2d6d6d',
        '--input-bg': '#1a3a3a',
        '--scrollbar-bg': '#2d6d6d',
        '--scrollbar-thumb': '#4d8d8d',
        '--card-bg': '#1a3a3a',
        '--bg-card': '#1a3a3a',
        '--bg-light': '#1a3a3a',
        '--bg-hover': '#2d6d6d'
    },
    'indigo': {
        '--primary-color': '#6366f1',
        '--secondary-color': '#818cf8',
        '--bg-color': '#0a0a1a',
        '--sidebar-bg': '#0f0f2a',
        '--message-bg': '#1a1a3a',
        '--user-message-bg': '#2d2d6d',
        '--border-color': '#2d2d6d',
        '--text-color': '#ececec',
        '--text-primary': '#ececec',
        '--text-secondary': '#8e8e8e',
        '--hover-bg': '#2d2d6d',
        '--input-bg': '#1a1a3a',
        '--scrollbar-bg': '#2d2d6d',
        '--scrollbar-thumb': '#4d4d8d',
        '--card-bg': '#1a1a3a',
        '--bg-card': '#1a1a3a',
        '--bg-light': '#1a1a3a',
        '--bg-hover': '#2d2d6d'
    }
}

@app.route('/api/theme/css-vars')
def get_theme_css_vars():
    """获取当前用户主题的CSS变量"""
    theme = 'dark'
    if 'username' in session:
        username = session['username']
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT theme FROM users WHERE username = %s", (username,))
                    user = cursor.fetchone()
                    if user:
                        theme = user.get('theme', 'dark')
        except Exception:
            pass
    
    css_vars = THEME_CSS_VARS.get(theme, THEME_CSS_VARS['dark'])
    
    css_text = ':root {\n'
    for key, value in css_vars.items():
        css_text += f'    {key}: {value};\n'
    css_text += '}'
    
    response = make_response(css_text)
    response.headers['Content-Type'] = 'text/css; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/theme/vars')
def get_theme_vars_json():
    """获取当前用户主题的CSS变量（JSON格式）"""
    theme = 'dark'
    if 'username' in session:
        username = session['username']
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT theme FROM users WHERE username = %s", (username,))
                    user = cursor.fetchone()
                    if user:
                        theme = user.get('theme', 'dark')
        except Exception:
            pass
    
    return jsonify({
        'theme': theme,
        'css_vars': THEME_CSS_VARS.get(theme, THEME_CSS_VARS['dark'])
    })

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
        agent_id = data.get('agent_id')
        system_prompt = data.get('system_prompt', '')
        username = session['username']
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 如果有agent_id，获取Agent信息
        print(f'[Chat] agent_id={agent_id}, 前端system_prompt长度={len(system_prompt)}')
        if agent_id:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM agents WHERE id = %s AND username = %s",
                        (agent_id, username)
                    )
                    agent = cursor.fetchone()
                    if agent:
                        model = agent.get('model', model)
                        print(f'[Chat] agent.system_prompt长度={len(agent.get("system_prompt", ""))}, prompt_id={agent.get("prompt_id")}')
                        if agent.get('system_prompt'):
                            system_prompt = agent['system_prompt']
                            print(f'[Chat] 使用agent.system_prompt')
                        elif agent.get('prompt_id'):
                            cursor.execute(
                                "SELECT content FROM prompts WHERE id = %s AND username = %s",
                                (agent['prompt_id'], username)
                            )
                            prompt = cursor.fetchone()
                            if prompt:
                                system_prompt = prompt['content']
                                print(f'[Chat] 通过prompt_id={agent.get("prompt_id")}获取提示词')
        
        # 获取对话历史
        messages = get_conversation_from_db(conversation_id, username)
        
        # 获取用户信息并注入到context中
        user_info = get_user_info_for_context(username)
        if user_info:
            messages.insert(0, {
                'role': 'system',
                'content': user_info,
                'timestamp': datetime.now().isoformat()
            })
        
        # 如果有system_prompt，添加到消息开头
        if system_prompt:
            messages.insert(0, {
                'role': 'system',
                'content': system_prompt,
                'timestamp': datetime.now().isoformat()
            })
        
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
                    if msg['role'] in ['system', 'user', 'assistant']
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
                
                # 如果有中间 content，先发送给前端
                if response_message.content:
                    yield f"data: {json.dumps({'content': response_message.content})}\n\n"
                    full_response += response_message.content
                
                if tool_calls:
                    # 保存带 tool_calls 的助手消息到数据库
                    messages.append({
                        'role': 'assistant',
                        'content': full_response,
                        'tool_calls': [{
                            'id': tc.id,
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        } for tc in (tool_calls if isinstance(tool_calls, list) else [tool_calls])]
                    })
                    
                    # AI 决定调用技能
                    api_messages.append(response_message)
                    
                    # 循环处理多轮 tool_calls
                    needs_stream = False
                    while tool_calls:
                        # 执行所有被调用的技能
                        for tool_call in tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            function_args['_username'] = username
                            
                            # 发送思考过程：正在调用函数
                            yield f"data: {json.dumps({'thinking': {'type': 'calling_function', 'function': function_name, 'args': function_args}})}\n\n"
                            
                            # 执行技能
                            result = skill_registry.execute_skill(function_name, **function_args)
                            
                            # 发送思考过程：函数执行结果
                            yield f"data: {json.dumps({'thinking': {'type': 'function_result', 'function': function_name, 'result': result}})}\n\n"
                            
                            # 将技能执行结果添加到消息中
                            tool_result_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps(result, ensure_ascii=False)
                            }
                            api_messages.append(tool_result_msg)
                            messages.append(tool_result_msg)
                        
                        # 再次调用 API 获取回复（可能还有更多 tool_calls）
                        response = client.chat.completions.create(
                            model=model,
                            messages=api_messages,
                            tools=tools if tools else None,
                            tool_choice="auto" if tools else None,
                            temperature=0.7,
                            max_tokens=2000
                        )
                        
                        response_message = response.choices[0].message
                        tool_calls = response_message.tool_calls
                        
                        # 如果没有更多 tool_calls 了，准备使用流式获取最终回复
                        if not tool_calls:
                            needs_stream = True
                            break
                        
                        # 还有更多 tool_calls
                        api_messages.append(response_message)
                        messages.append({
                            'role': 'assistant',
                            'content': response_message.content or '',
                            'tool_calls': [{
                                'id': tc.id,
                                'function': {
                                    'name': tc.function.name,
                                    'arguments': tc.function.arguments
                                }
                            } for tc in (tool_calls if isinstance(tool_calls, list) else [tool_calls])]
                        })
                    
                    # 使用流式 API 获取最终回复
                    if needs_stream:
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
    """列出对话，支持分页"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as total FROM conversations WHERE username = %s",
                (username,)
            )
            total = cursor.fetchone()['total']
            
            cursor.execute(
                "SELECT conversation_id, messages, updated_at FROM conversations WHERE username = %s ORDER BY updated_at DESC LIMIT %s OFFSET %s",
                (username, limit, offset)
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
    
    has_more = (offset + len(results)) < total
    
    return jsonify({
        'conversations': conversation_list,
        'total': total,
        'page': page,
        'limit': limit,
        'has_more': has_more
    })

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

@app.route('/api/skills/scan', methods=['GET'])
def scan_skills():
    """扫描并重新加载skills目录下所有技能"""
    global skill_registry
    
    try:
        skill_registry = register_all_skills()
        
        user_settings = {}
        username = session.get('username')
        if username:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT skill_name, enabled FROM user_skills WHERE username = %s",
                        (username,)
                    )
                    user_settings = {row['skill_name']: bool(row['enabled']) for row in cursor.fetchall()}
        
        skills = []
        for skill_name in skill_registry.list_skills():
            skill = skill_registry.get_skill(skill_name)
            if skill:
                enabled = user_settings.get(skill_name, True)
                skills.append({
                    'name': skill.name,
                    'description': skill.description,
                    'parameters': skill.parameters,
                    'enabled': enabled
                })
        
        return jsonify({
            'success': True,
            'skills': skills,
            'count': len(skills)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

# ==================================================
# 工作流 API
# ==================================================

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """获取用户的工作流列表"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, status, created_at, updated_at "
                    "FROM workflows WHERE username = %s ORDER BY updated_at DESC",
                    (username,)
                )
                workflows = cursor.fetchall()
                
                # 转换日期格式为字符串
                for wf in workflows:
                    for field in ['created_at', 'updated_at']:
                        if wf[field] and isinstance(wf[field], datetime):
                            wf[field] = wf[field].isoformat()
                
                return jsonify({'workflows': workflows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/search', methods=['GET'])
def search_workflows():
    """搜索工作流"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    # 获取搜索参数
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '')
    creator = request.args.get('creator', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    sort_by = request.args.get('sort_by', 'relevance')
    sort_order = request.args.get('sort_order', 'desc')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    # 验证排序参数
    valid_sort_by = ['relevance', 'created_at', 'updated_at', 'name']
    valid_sort_order = ['asc', 'desc']
    if sort_by not in valid_sort_by:
        sort_by = 'relevance'
    if sort_order not in valid_sort_order:
        sort_order = 'desc'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 构建查询条件
                conditions = ["username = %s"]
                params = [username]
                
                # 关键词模糊搜索
                if keyword:
                    conditions.append("(name LIKE %s OR description LIKE %s)")
                    keyword_pattern = f"%{keyword}%"
                    params.extend([keyword_pattern, keyword_pattern])
                
                # 状态筛选
                if status:
                    conditions.append("status = %s")
                    params.append(status)
                
                # 创建者筛选（支持模糊匹配）
                if creator:
                    conditions.append("username LIKE %s")
                    params.append(f"%{creator}%")
                
                # 创建时间范围筛选
                if date_from:
                    conditions.append("created_at >= %s")
                    params.append(date_from)
                if date_to:
                    conditions.append("created_at <= %s")
                    params.append(date_to + ' 23:59:59')
                
                where_clause = " AND ".join(conditions)
                
                count_params = params.copy()
                
                # 构建排序逻辑
                if sort_by == 'relevance':
                    if keyword:
                        # 按相关度排序：名称匹配优先，然后是描述匹配
                        order_clause = f"CASE WHEN name LIKE %s THEN 0 ELSE 1 END, "
                        keyword_starts = f"{keyword}%"
                        params.append(keyword_starts)
                    else:
                        order_clause = ""
                    order_clause += "updated_at DESC" if sort_order == 'desc' else "updated_at ASC"
                elif sort_by == 'name':
                    order_clause = f"name {sort_order.upper()}, updated_at DESC"
                else:
                    order_clause = f"{sort_by} {sort_order.upper()}"
                
                # 查询总数 - 使用独立的params副本
                count_sql = f"SELECT COUNT(*) as total FROM workflows WHERE {where_clause}"
                cursor.execute(count_sql, count_params)
                total = cursor.fetchone()['total']
                
                # 分页查询
                offset = (page - 1) * page_size
                sql = f"""
                    SELECT id, name, description, status, username, created_at, updated_at 
                    FROM workflows 
                    WHERE {where_clause} 
                    ORDER BY {order_clause} 
                    LIMIT %s OFFSET %s
                """
                params.append(page_size)
                params.append(offset)
                
                cursor.execute(sql, params)
                workflows = cursor.fetchall()
                
                # 转换日期格式
                for wf in workflows:
                    for field in ['created_at', 'updated_at']:
                        if wf[field] and isinstance(wf[field], datetime):
                            wf[field] = wf[field].isoformat()
                
                # 如果有关键词，记录搜索历史
                if keyword:
                    # 记录搜索历史
                    cursor.execute(
                        "INSERT INTO workflow_search_history (username, search_keyword) VALUES (%s, %s)",
                        (username, keyword)
                    )
                    
                    # 更新热门搜索
                    cursor.execute("""
                        INSERT INTO popular_searches (keyword, search_type, search_count, last_searched_at)
                        VALUES (%s, 'workflow', 1, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE 
                            search_count = search_count + 1,
                            last_searched_at = CURRENT_TIMESTAMP
                    """, (keyword,))
                    
                    conn.commit()
                
                return jsonify({
                    'workflows': workflows,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/search/history', methods=['GET'])
def get_search_history():
    """获取用户搜索历史"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    limit = int(request.args.get('limit', 10))
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT search_keyword, MAX(search_time) as last_search_time
                    FROM workflow_search_history 
                    WHERE username = %s 
                    GROUP BY search_keyword 
                    ORDER BY last_search_time DESC 
                    LIMIT %s
                """, (username, limit))
                history = cursor.fetchall()
                
                return jsonify({'history': [h['search_keyword'] for h in history]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/search/history', methods=['DELETE'])
def clear_search_history():
    """清除用户搜索历史"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM workflow_search_history WHERE username = %s",
                    (username,)
                )
                conn.commit()
                
                return jsonify({'success': True, 'message': '搜索历史已清除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/search/popular', methods=['GET'])
def get_popular_searches():
    """获取热门搜索"""
    limit = int(request.args.get('limit', 10))
    search_type = request.args.get('type', 'workflow')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT keyword, search_count, last_searched_at
                    FROM popular_searches 
                    WHERE search_type = %s
                    ORDER BY search_count DESC, last_searched_at DESC 
                    LIMIT %s
                """, (search_type, limit))
                popular = cursor.fetchall()
                
                return jsonify({'popular': [
                    {
                        'keyword': p['keyword'],
                        'count': p['search_count']
                    } for p in popular
                ]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    """创建新的工作流"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'error': '工作流名称不能为空'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO workflows (name, description, username, status) VALUES (%s, %s, %s, %s)",
                    (name, description, username, 'draft')
                )
                workflow_id = cursor.lastrowid
                conn.commit()
                
                # 获取创建的工作流
                cursor.execute(
                    "SELECT id, name, description, status, created_at, updated_at FROM workflows WHERE id = %s",
                    (workflow_id,)
                )
                workflow = cursor.fetchone()
                
                # 转换日期格式
                for field in ['created_at', 'updated_at']:
                    if workflow[field] and isinstance(workflow[field], datetime):
                        workflow[field] = workflow[field].isoformat()
                
                return jsonify({'workflow': workflow})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """获取工作流详情（包括节点和边）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 获取工作流基本信息
                cursor.execute(
                    "SELECT id, name, description, status, definition, created_at, updated_at "
                    "FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                workflow = cursor.fetchone()
                
                if not workflow:
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 获取节点
                cursor.execute(
                    "SELECT id, node_id, node_type, name, config, position_x, position_y, created_at, updated_at "
                    "FROM workflow_nodes WHERE workflow_id = %s",
                    (workflow_id,)
                )
                nodes = cursor.fetchall()
                
                # 获取边
                cursor.execute(
                    "SELECT id, source_node_id, target_node_id, `condition` FROM workflow_edges WHERE workflow_id = %s",
                    (workflow_id,)
                )
                edges = cursor.fetchall()
                
                # 转换日期格式
                for field in ['created_at', 'updated_at']:
                    if workflow[field] and isinstance(workflow[field], datetime):
                        workflow[field] = workflow[field].isoformat()
                
                for node in nodes:
                    for field in ['created_at', 'updated_at']:
                        if node[field] and isinstance(node[field], datetime):
                            node[field] = node[field].isoformat()
                
                return jsonify({
                    'workflow': workflow,
                    'nodes': nodes,
                    'edges': edges
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """更新工作流"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 构建更新字段
                update_fields = []
                params = []
                
                if 'name' in data:
                    name = data['name'].strip()
                    if name:
                        update_fields.append("name = %s")
                        params.append(name)
                
                if 'description' in data:
                    update_fields.append("description = %s")
                    params.append(data['description'].strip())
                
                if 'status' in data and data['status'] in ['draft', 'active', 'paused', 'archived']:
                    update_fields.append("status = %s")
                    params.append(data['status'])
                
                if 'definition' in data:
                    update_fields.append("definition = %s")
                    params.append(json.dumps(data['definition']))
                
                if not update_fields:
                    return jsonify({'error': '没有提供更新字段'}), 400
                
                # 执行更新
                params.append(workflow_id)
                params.append(username)
                
                cursor.execute(
                    f"UPDATE workflows SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s AND username = %s",
                    tuple(params)
                )
                conn.commit()
                
                # 获取更新后的工作流
                cursor.execute(
                    "SELECT id, name, description, status, created_at, updated_at FROM workflows WHERE id = %s",
                    (workflow_id,)
                )
                workflow = cursor.fetchone()
                
                # 转换日期格式
                for field in ['created_at', 'updated_at']:
                    if workflow[field] and isinstance(workflow[field], datetime):
                        workflow[field] = workflow[field].isoformat()
                
                return jsonify({'workflow': workflow})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """删除工作流"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查工作流是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 删除工作流（级联删除相关节点和边）
                cursor.execute("DELETE FROM workflows WHERE id = %s", (workflow_id,))
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/workflows/<int:workflow_id>/nodes', methods=['GET'])
def get_workflow_nodes(workflow_id):
    """获取工作流所有节点"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 获取所有节点
                cursor.execute(
                    "SELECT id, node_id, node_type, name, config, position_x, position_y, created_at, updated_at "
                    "FROM workflow_nodes WHERE workflow_id = %s ORDER BY created_at",
                    (workflow_id,)
                )
                nodes = cursor.fetchall()
                
                # 转换日期格式和配置字段
                for node in nodes:
                    for field in ['created_at', 'updated_at']:
                        if node[field] and isinstance(node[field], datetime):
                            node[field] = node[field].isoformat()
                    # 确保config是字符串（JSON）
                    if node['config'] and isinstance(node['config'], str):
                        try:
                            node['config'] = json.loads(node['config'])
                        except:
                            node['config'] = {}
                
                return jsonify(nodes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/nodes', methods=['POST'])
def create_workflow_node(workflow_id):
    """创建工作流节点"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        node_id = data.get('node_id', str(uuid.uuid4())[:8])
        node_type = data.get('node_type', '')
        name = data.get('name', '').strip()
        config = data.get('config', {})
        position_x = data.get('position_x', 0)
        position_y = data.get('position_y', 0)
        
        if not node_type or node_type not in ['start', 'end', 'llm', 'script', 'condition', 'input', 'output', 'delay']:
            return jsonify({'error': '无效的节点类型'}), 400
        
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 插入节点
                cursor.execute(
                    "INSERT INTO workflow_nodes (workflow_id, node_id, node_type, name, config, position_x, position_y) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (workflow_id, node_id, node_type, name, json.dumps(config), position_x, position_y)
                )
                node_db_id = cursor.lastrowid
                conn.commit()
                
                # 获取创建的节点
                cursor.execute(
                    "SELECT id, node_id, node_type, name, config, position_x, position_y, created_at, updated_at "
                    "FROM workflow_nodes WHERE id = %s",
                    (node_db_id,)
                )
                node = cursor.fetchone()
                
                # 转换日期格式
                for field in ['created_at', 'updated_at']:
                    if node[field] and isinstance(node[field], datetime):
                        node[field] = node[field].isoformat()
                
                return jsonify({'node': node})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/nodes/<node_id>', methods=['PUT'])
def update_workflow_node(workflow_id, node_id):
    """更新工作流节点"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 构建更新字段
                update_fields = ["updated_at = CURRENT_TIMESTAMP"]
                params = []
                
                if 'name' in data:
                    update_fields.append("name = %s")
                    params.append(data['name'].strip())
                
                if 'config' in data:
                    update_fields.append("config = %s")
                    params.append(json.dumps(data['config']))
                
                if 'position_x' in data:
                    update_fields.append("position_x = %s")
                    params.append(data['position_x'])
                
                if 'position_y' in data:
                    update_fields.append("position_y = %s")
                    params.append(data['position_y'])
                
                if len(update_fields) == 1:  # 只有 updated_at
                    return jsonify({'error': '没有提供更新字段'}), 400
                
                # 执行更新
                params.append(workflow_id)
                params.append(node_id)
                
                cursor.execute(
                    f"UPDATE workflow_nodes SET {', '.join(update_fields)} "
                    "WHERE workflow_id = %s AND node_id = %s",
                    tuple(params)
                )
                conn.commit()
                
                # 获取更新后的节点
                cursor.execute(
                    "SELECT id, node_id, node_type, name, config, position_x, position_y, created_at, updated_at "
                    "FROM workflow_nodes WHERE workflow_id = %s AND node_id = %s",
                    (workflow_id, node_id)
                )
                node = cursor.fetchone()
                
                if not node:
                    return jsonify({'error': '节点不存在'}), 404
                
                # 转换日期格式
                for field in ['created_at', 'updated_at']:
                    if node[field] and isinstance(node[field], datetime):
                        node[field] = node[field].isoformat()
                
                return jsonify({'node': node})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/nodes/<node_id>', methods=['DELETE'])
def delete_workflow_node(workflow_id, node_id):
    """删除工作流节点"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 删除节点
                cursor.execute(
                    "DELETE FROM workflow_nodes WHERE workflow_id = %s AND node_id = %s",
                    (workflow_id, node_id)
                )
                # 同时删除相关的边
                cursor.execute(
                    "DELETE FROM workflow_edges WHERE workflow_id = %s AND (source_node_id = %s OR target_node_id = %s)",
                    (workflow_id, node_id, node_id)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/workflows/<int:workflow_id>/edges', methods=['GET'])
def get_workflow_edges(workflow_id):
    """获取工作流所有边（连接）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 获取所有边
                cursor.execute(
                    "SELECT id, source_node_id, target_node_id, `condition`, created_at "
                    "FROM workflow_edges WHERE workflow_id = %s ORDER BY created_at",
                    (workflow_id,)
                )
                edges = cursor.fetchall()
                
                # 转换日期格式
                for edge in edges:
                    if edge['created_at'] and isinstance(edge['created_at'], datetime):
                        edge['created_at'] = edge['created_at'].isoformat()
                
                return jsonify(edges)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/edges', methods=['POST'])
def create_workflow_edge(workflow_id):
    """创建工作流边（连接节点）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        source_node_id = data.get('source_node_id', '')
        target_node_id = data.get('target_node_id', '')
        condition = data.get('condition', '')
        
        if not source_node_id or not target_node_id:
            return jsonify({'error': '源节点和目标节点不能为空'}), 400
        
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 插入边
                cursor.execute(
                    "INSERT INTO workflow_edges (workflow_id, source_node_id, target_node_id, `condition`) "
                    "VALUES (%s, %s, %s, %s)",
                    (workflow_id, source_node_id, target_node_id, condition)
                )
                edge_id = cursor.lastrowid
                conn.commit()
                
                return jsonify({
                    'edge': {
                        'id': edge_id,
                        'workflow_id': workflow_id,
                        'source_node_id': source_node_id,
                        'target_node_id': target_node_id,
                        'condition': condition
                    }
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/edges/<int:edge_id>', methods=['DELETE'])
def delete_workflow_edge(workflow_id, edge_id):
    """删除工作流边"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 删除边
                cursor.execute(
                    "DELETE FROM workflow_edges WHERE id = %s AND workflow_id = %s",
                    (edge_id, workflow_id)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/start', methods=['POST'])
def start_workflow(workflow_id):
    """启动工作流（将状态改为active）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE workflows SET status = 'active', updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                conn.commit()
                
                return jsonify({'success': True, 'status': 'active'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/pause', methods=['POST'])
def pause_workflow(workflow_id):
    """暂停工作流（将状态改为paused）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE workflows SET status = 'paused', updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                conn.commit()
                
                return jsonify({'success': True, 'status': 'paused'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """执行工作流"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        data = request.json
        input_data = data.get('input', {})
        
        # 检查工作流是否存在且用户有权访问
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, status FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                workflow = cursor.fetchone()
                
                if not workflow:
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 创建工作流执行记录
                execution_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO workflow_executions (workflow_id, username, execution_id, status, input_data) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (workflow_id, username, execution_id, 'pending', json.dumps(input_data))
                )
                execution_db_id = cursor.lastrowid
                
                # 获取工作流节点
                cursor.execute(
                    "SELECT node_id, node_type, name, config FROM workflow_nodes WHERE workflow_id = %s",
                    (workflow_id,)
                )
                nodes = cursor.fetchall()
                
                # 创建工作流节点执行记录
                for node in nodes:
                    cursor.execute(
                        "INSERT INTO workflow_node_executions (execution_id, node_id, node_type, status) "
                        "VALUES (%s, %s, %s, %s)",
                        (execution_db_id, node['node_id'], node['node_type'], 'pending')
                    )
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'execution_id': execution_id,
                    'execution_db_id': execution_db_id,
                    'message': '工作流执行已创建'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>/executions', methods=['GET'])
def get_workflow_executions(workflow_id):
    """获取工作流的执行记录"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查工作流是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM workflows WHERE id = %s AND username = %s",
                    (workflow_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '工作流不存在或无权访问'}), 404
                
                # 获取执行记录
                cursor.execute(
                    "SELECT id, execution_id, status, input_data, output_data, error_message, "
                    "started_at, completed_at, created_at, updated_at "
                    "FROM workflow_executions WHERE workflow_id = %s ORDER BY created_at DESC LIMIT 50",
                    (workflow_id,)
                )
                executions = cursor.fetchall()
                
                # 转换日期格式和JSON字段
                for exe in executions:
                    for field in ['started_at', 'completed_at', 'created_at', 'updated_at']:
                        if exe[field] and isinstance(exe[field], datetime):
                            exe[field] = exe[field].isoformat()
                    
                    for field in ['input_data', 'output_data']:
                        if exe[field] and isinstance(exe[field], str):
                            try:
                                exe[field] = json.loads(exe[field])
                            except:
                                exe[field] = None
                
                return jsonify({'executions': executions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    """获取用户的定时任务列表（支持分页和搜索）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str)
    
    # 限制每页最大数量
    page_size = min(page_size, 100)
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 构建搜索条件
                search_condition = ""
                search_params = [username]
                if search:
                    search_condition = " AND (name LIKE %s OR description LIKE %s OR cron LIKE %s OR command LIKE %s)"
                    search_pattern = f"%{search}%"
                    search_params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
                
                # 查询总数
                count_sql = f"SELECT COUNT(*) as total FROM schedules WHERE username = %s{search_condition}"
                cursor.execute(count_sql, tuple(search_params))
                total = cursor.fetchone()['total']
                
                # 查询数据
                sql = f"""
                    SELECT id, name, description, cron, preset, command, status, 
                           last_run_at, next_run_at, created_at, updated_at 
                    FROM schedules 
                    WHERE username = %s{search_condition} 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """
                search_params.extend([page_size, offset])
                cursor.execute(sql, tuple(search_params))
                schedules = cursor.fetchall()
                
                # 转换日期格式
                for schedule in schedules:
                    for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
                        if schedule[field] and isinstance(schedule[field], datetime):
                            schedule[field] = schedule[field].isoformat()
                
                return jsonify({
                    'schedules': schedules,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """创建新的定时任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    # 验证必要字段
    required_fields = ['name', 'cron', 'command']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'缺少必要字段: {field}'}), 400
    
    try:
        from croniter import croniter
        from datetime import datetime
        
        cron_str = data['cron']
        next_run = None
        
        if data.get('status', 'active') == 'active':
            try:
                cron = croniter(cron_str, datetime.now())
                next_run = cron.get_next(datetime)
            except Exception as e:
                print(f"Cron 解析错误: {e}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO schedules (name, description, username, cron, preset, command, status, next_run_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        data['name'],
                        data.get('description', ''),
                        username,
                        data['cron'],
                        data.get('preset', ''),
                        data['command'],
                        data.get('status', 'active'),
                        next_run
                    )
                )
                schedule_id = cursor.lastrowid
                conn.commit()
                
                # 返回新创建的定时任务
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE id = %s",
                    (schedule_id,)
                )
                schedule = cursor.fetchone()
                if schedule:
                    for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
                        if schedule[field] and isinstance(schedule[field], datetime):
                            schedule[field] = schedule[field].isoformat()
                
                return jsonify(schedule), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """更新定时任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查定时任务是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '定时任务不存在或无权访问'}), 404
                
                # 构建更新语句
                update_fields = []
                update_values = []
                
                if 'name' in data:
                    update_fields.append("name = %s")
                    update_values.append(data['name'])
                if 'description' in data:
                    update_fields.append("description = %s")
                    update_values.append(data['description'])
                if 'cron' in data:
                    update_fields.append("cron = %s")
                    update_values.append(data['cron'])
                if 'preset' in data:
                    update_fields.append("preset = %s")
                    update_values.append(data['preset'])
                if 'command' in data:
                    update_fields.append("command = %s")
                    update_values.append(data['command'])
                if 'status' in data:
                    update_fields.append("status = %s")
                    update_values.append(data['status'])
                
                if not update_fields:
                    return jsonify({'error': '没有提供更新字段'}), 400
                
                update_values.append(schedule_id)
                update_values.append(username)
                
                cursor.execute(
                    f"UPDATE schedules SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s AND username = %s",
                    tuple(update_values)
                )
                conn.commit()
                
                if 'cron' in data or 'status' in data:
                    cursor.execute(
                        "SELECT cron, status FROM schedules WHERE id = %s",
                        (schedule_id,)
                    )
                    schedule = cursor.fetchone()
                    if schedule and schedule['status'] == 'active':
                        try:
                            from croniter import croniter
                            cron = croniter(schedule['cron'], datetime.now())
                            next_run = cron.get_next(datetime)
                            cursor.execute(
                                "UPDATE schedules SET next_run_at = %s WHERE id = %s",
                                (next_run, schedule_id)
                            )
                            conn.commit()
                        except Exception as e:
                            print(f"更新下次执行时间失败: {e}")
                
                # 返回更新后的定时任务
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE id = %s",
                    (schedule_id,)
                )
                schedule = cursor.fetchone()
                if schedule:
                    for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
                        if schedule[field] and isinstance(schedule[field], datetime):
                            schedule[field] = schedule[field].isoformat()
                
                return jsonify(schedule)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除定时任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查定时任务是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '定时任务不存在或无权访问'}), 404
                
                cursor.execute(
                    "DELETE FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>/executions', methods=['GET'])
def get_schedule_executions(schedule_id):
    """获取定时任务的执行记录"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查定时任务是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '定时任务不存在或无权访问'}), 404
                
                # 获取执行记录
                cursor.execute(
                    "SELECT id, schedule_id, execution_id, status, output, error_message, "
                    "started_at, completed_at, created_at "
                    "FROM schedule_executions WHERE schedule_id = %s ORDER BY created_at DESC LIMIT 50",
                    (schedule_id,)
                )
                executions = cursor.fetchall()
                
                # 转换日期格式
                for exe in executions:
                    for field in ['started_at', 'completed_at', 'created_at']:
                        if exe[field] and isinstance(exe[field], datetime):
                            exe[field] = exe[field].isoformat()
                
                return jsonify({'executions': executions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def execute_schedule_command(schedule_id, execution_id, command):
    """执行定时任务命令并更新状态（在后台线程中运行）"""
    try:
        # 更新状态为运行中
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE schedule_executions SET status = 'running', started_at = CURRENT_TIMESTAMP "
                    "WHERE execution_id = %s",
                    (execution_id,)
                )
                conn.commit()
        
        # 执行命令（安全警告：这可能会执行任意命令，请谨慎使用）
        # 这里使用子进程执行命令，设置超时防止无限阻塞
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            cwd=os.getcwd()  # 在当前工作目录执行
        )
        
        # 更新执行结果
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if result.returncode == 0:
                    status = 'completed'
                    output = result.stdout
                    error_message = None
                else:
                    status = 'failed'
                    output = result.stdout
                    error_message = result.stderr
                
                cursor.execute(
                    "UPDATE schedule_executions SET status = %s, output = %s, error_message = %s, completed_at = CURRENT_TIMESTAMP "
                    "WHERE execution_id = %s",
                    (status, output, error_message, execution_id)
                )
                conn.commit()
                
    except subprocess.TimeoutExpired:
        # 命令执行超时
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE schedule_executions SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP "
                    "WHERE execution_id = %s",
                    ("命令执行超时（5分钟）", execution_id)
                )
                conn.commit()
    except Exception as e:
        # 其他错误
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE schedule_executions SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP "
                    "WHERE execution_id = %s",
                    (str(e), execution_id)
                )
                conn.commit()

@app.route('/api/schedules/<int:schedule_id>/execute', methods=['POST'])
def execute_schedule(schedule_id):
    """手动执行定时任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查定时任务是否存在且用户有权访问
                cursor.execute(
                    "SELECT id, name, command FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                schedule = cursor.fetchone()
                
                if not schedule:
                    return jsonify({'error': '定时任务不存在或无权访问'}), 404
                
                # 创建执行记录
                execution_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO schedule_executions (schedule_id, username, execution_id, status) "
                    "VALUES (%s, %s, %s, %s)",
                    (schedule_id, username, execution_id, 'pending')
                )
                execution_db_id = cursor.lastrowid
                
                # 更新定时任务的最后运行时间
                cursor.execute(
                    "UPDATE schedules SET last_run_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = %s",
                    (schedule_id,)
                )
                
                conn.commit()
                
                # 在后台线程中执行命令
                command = schedule['command']
                thread = threading.Thread(
                    target=execute_schedule_command,
                    args=(schedule_id, execution_id, command)
                )
                thread.daemon = True  # 设置为守护线程，主程序退出时会自动结束
                thread.start()
                
                return jsonify({
                    'success': True,
                    'execution_id': execution_id,
                    'execution_db_id': execution_db_id,
                    'message': '定时任务执行已启动，正在后台运行'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>/executions/<execution_id>', methods=['PUT'])
def update_schedule_execution(schedule_id, execution_id):
    """更新定时任务执行记录状态"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查执行记录是否存在且用户有权访问
                cursor.execute(
                    "SELECT id FROM schedule_executions WHERE execution_id = %s AND username = %s AND schedule_id = %s",
                    (execution_id, username, schedule_id)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '执行记录不存在或无权访问'}), 404
                
                # 构建更新语句
                update_fields = []
                update_values = []
                
                if 'status' in data:
                    update_fields.append("status = %s")
                    update_values.append(data['status'])
                
                if 'output' in data:
                    update_fields.append("output = %s")
                    update_values.append(data['output'])
                
                if 'error_message' in data:
                    update_fields.append("error_message = %s")
                    update_values.append(data['error_message'])
                
                if 'started_at' in data:
                    update_fields.append("started_at = %s")
                    update_values.append(data['started_at'])
                
                if 'completed_at' in data:
                    update_fields.append("completed_at = %s")
                    update_values.append(data['completed_at'])
                
                if not update_fields:
                    return jsonify({'error': '没有提供更新字段'}), 400
                
                update_values.append(execution_id)
                update_values.append(username)
                update_values.append(schedule_id)
                
                cursor.execute(
                    f"UPDATE schedule_executions SET {', '.join(update_fields)} "
                    "WHERE execution_id = %s AND username = %s AND schedule_id = %s",
                    tuple(update_values)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 异步任务 API ====================

@app.route('/api/async_tasks', methods=['GET'])
def get_async_tasks():
    """获取用户的异步任务列表（支持分页和搜索）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str)
    
    # 限制每页最大数量
    page_size = min(page_size, 100)
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 构建搜索条件
                search_condition = ""
                search_params = [username]
                if search:
                    search_condition = " AND (task_name LIKE %s OR description LIKE %s OR command LIKE %s OR status LIKE %s)"
                    search_pattern = f"%{search}%"
                    search_params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
                
                # 查询总数
                count_sql = f"SELECT COUNT(*) as total FROM async_tasks WHERE username = %s{search_condition}"
                cursor.execute(count_sql, tuple(search_params))
                total = cursor.fetchone()['total']
                
                # 查询数据
                sql = f"""
                    SELECT id, task_name, description, command, status, output, error_message, 
                           execution_id, created_at, updated_at, started_at, completed_at 
                    FROM async_tasks 
                    WHERE username = %s{search_condition} 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """
                search_params.extend([page_size, offset])
                cursor.execute(sql, tuple(search_params))
                tasks = cursor.fetchall()
                
                # 转换日期格式
                for task in tasks:
                    for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                        if task[field] and isinstance(task[field], datetime):
                            task[field] = task[field].isoformat()
                
                return jsonify({
                    'tasks': tasks,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks', methods=['POST'])
def create_async_task():
    """创建新的异步任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    # 验证必要字段
    required_fields = ['task_name', 'command']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'缺少必要字段: {field}'}), 400
    
    try:
        import uuid
        import threading
        from datetime import datetime, timedelta
        
        execution_id = str(uuid.uuid4())
        task_name = data['task_name']
        description = data.get('description', '')
        command = data['command']
        delay_minutes = int(data.get('delay_minutes', 0))
        if delay_minutes < 0:
            delay_minutes = 0
        
        if delay_minutes > 0:
            scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
            status = 'scheduled'
        else:
            scheduled_at = None
            status = 'pending'
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if scheduled_at:
                    cursor.execute(
                        "INSERT INTO async_tasks (username, task_name, description, command, status, execution_id, scheduled_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (username, task_name, description, command, status, execution_id, scheduled_at)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO async_tasks (username, task_name, description, command, status, execution_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (username, task_name, description, command, status, execution_id)
                    )
                task_id = cursor.lastrowid
                conn.commit()
                
                # 如果立即执行，启动后台线程执行任务
                if status == 'pending':
                    thread = threading.Thread(
                        target=execute_async_task,
                        args=(task_id, execution_id, command),
                        daemon=True
                    )
                    thread.start()
                
                # 返回新创建的任务
                cursor.execute(
                    "SELECT id, task_name, description, command, status, execution_id, scheduled_at, created_at, updated_at, started_at, completed_at "
                    "FROM async_tasks WHERE id = %s",
                    (task_id,)
                )
                task = cursor.fetchone()
                if task:
                    for field in ['scheduled_at', 'created_at', 'updated_at', 'started_at', 'completed_at']:
                        if task[field] and isinstance(task[field], datetime):
                            task[field] = task[field].isoformat()
                
                return jsonify({'task': task}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks/<int:task_id>', methods=['GET'])
def get_async_task(task_id):
    """获取单个异步任务详情"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, task_name, description, command, status, output, error_message, execution_id, created_at, updated_at, started_at, completed_at "
                    "FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                task = cursor.fetchone()
                
                if not task:
                    return jsonify({'error': '任务不存在或无权访问'}), 404
                
                # 转换日期格式
                for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                    if task[field] and isinstance(task[field], datetime):
                        task[field] = task[field].isoformat()
                
                return jsonify({'task': task})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks/<int:task_id>', methods=['PUT'])
def update_async_task(task_id):
    """更新异步任务状态"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    # 只允许更新状态字段
    if 'status' not in data:
        return jsonify({'error': '缺少状态字段'}), 400
    
    allowed_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
    if data['status'] not in allowed_statuses:
        return jsonify({'error': '无效的状态值'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查任务是否存在且属于用户
                cursor.execute(
                    "SELECT id FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '任务不存在或无权访问'}), 404
                
                # 更新状态
                cursor.execute(
                    "UPDATE async_tasks SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (data['status'], task_id)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks/<int:task_id>/output', methods=['GET'])
def get_async_task_output(task_id):
    """获取异步任务的输出内容"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT output, error_message FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                task = cursor.fetchone()
                
                if not task:
                    return jsonify({'error': '任务不存在或无权访问'}), 404
                
                return jsonify({'output': task['output'], 'error_message': task['error_message']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks/<int:task_id>', methods=['DELETE'])
def delete_async_task(task_id):
    """删除异步任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查任务是否存在且属于用户
                cursor.execute(
                    "SELECT id FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '任务不存在或无权访问'}), 404
                
                # 删除任务
                cursor.execute(
                    "DELETE FROM async_tasks WHERE id = %s",
                    (task_id,)
                )
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/async_tasks/<int:task_id>/execute', methods=['POST'])
def execute_async_task_endpoint(task_id):
    """立即执行异步任务"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        import uuid
        import threading
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查任务是否存在且属于用户
                cursor.execute(
                    "SELECT id, command, status FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                task = cursor.fetchone()
                if not task:
                    return jsonify({'error': '任务不存在或无权访问'}), 404
                
                command = task['command']
                new_execution_id = str(uuid.uuid4())
                
                # 更新任务状态为 pending，设置新的 execution_id
                cursor.execute(
                    "UPDATE async_tasks SET status = 'pending', execution_id = %s, scheduled_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_execution_id, task_id)
                )
                conn.commit()
                
                # 启动后台线程执行任务
                thread = threading.Thread(
                    target=execute_async_task,
                    args=(task_id, new_execution_id, command),
                    daemon=True
                )
                thread.start()
                
                return jsonify({'success': True, 'message': '任务执行已启动', 'execution_id': new_execution_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 提示词管理 API ====================

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """获取提示词列表"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    search = request.args.get('search', '')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if search:
                    cursor.execute(
                        "SELECT * FROM prompts WHERE username = %s AND (name LIKE %s OR content LIKE %s OR tags LIKE %s) ORDER BY updated_at DESC",
                        (username, f'%{search}%', f'%{search}%', f'%{search}%')
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM prompts WHERE username = %s ORDER BY updated_at DESC",
                        (username,)
                    )
                prompts = cursor.fetchall()
                
                for prompt in prompts:
                    if prompt.get('tags'):
                        prompt['tags'] = prompt['tags'].split(',') if isinstance(prompt['tags'], str) else []
                    else:
                        prompt['tags'] = []
                
                return jsonify({'prompts': prompts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    """创建提示词"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()
    description = data.get('description', '').strip()
    tags = data.get('tags', [])
    
    if not name:
        return jsonify({'error': '提示词名称不能为空'}), 400
    if not content:
        return jsonify({'error': '提示词内容不能为空'}), 400
    
    tags_str = ','.join(tags) if isinstance(tags, list) else str(tags)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO prompts (name, content, description, username, tags) VALUES (%s, %s, %s, %s, %s)",
                    (name, content, description, username, tags_str)
                )
                conn.commit()
                prompt_id = cursor.lastrowid
                
                return jsonify({
                    'success': True,
                    'prompt': {
                        'id': prompt_id,
                        'name': name,
                        'content': content,
                        'description': description,
                        'tags': tags
                    }
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个提示词"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM prompts WHERE id = %s AND username = %s",
                    (prompt_id, username)
                )
                prompt = cursor.fetchone()
                
                if not prompt:
                    return jsonify({'error': '提示词不存在'}), 404
                
                if prompt.get('tags'):
                    prompt['tags'] = prompt['tags'].split(',') if isinstance(prompt['tags'], str) else []
                else:
                    prompt['tags'] = []
                
                return jsonify({'prompt': prompt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新提示词"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()
    description = data.get('description', '').strip()
    tags = data.get('tags', [])
    
    if not name:
        return jsonify({'error': '提示词名称不能为空'}), 400
    if not content:
        return jsonify({'error': '提示词内容不能为空'}), 400
    
    tags_str = ','.join(tags) if isinstance(tags, list) else str(tags)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE prompts SET name = %s, content = %s, description = %s, tags = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s AND username = %s",
                    (name, content, description, tags_str, prompt_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': '提示词不存在'}), 404
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """删除提示词"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM prompts WHERE id = %s AND username = %s",
                    (prompt_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': '提示词不存在'}), 404
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Agent管理 API ====================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """获取Agent列表"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    search = request.args.get('search', '')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if search:
                    cursor.execute(
                        """SELECT a.*, p.name as prompt_name, 
                           GROUP_CONCAT(asl.skill_name ORDER BY asl.skill_name) as skills
                           FROM agents a 
                           LEFT JOIN prompts p ON a.prompt_id = p.id 
                           LEFT JOIN agent_skills asl ON a.id = asl.agent_id
                           WHERE a.username = %s AND (a.name LIKE %s OR a.description LIKE %s) 
                           GROUP BY a.id
                           ORDER BY a.updated_at DESC""",
                        (username, f'%{search}%', f'%{search}%')
                    )
                else:
                    cursor.execute(
                        """SELECT a.*, p.name as prompt_name,
                           GROUP_CONCAT(asl.skill_name ORDER BY asl.skill_name) as skills
                           FROM agents a 
                           LEFT JOIN prompts p ON a.prompt_id = p.id 
                           LEFT JOIN agent_skills asl ON a.id = asl.agent_id
                           WHERE a.username = %s 
                           GROUP BY a.id
                           ORDER BY a.updated_at DESC""",
                        (username,)
                    )
                agents = cursor.fetchall()
                return jsonify({'agents': agents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents', methods=['POST'])
def create_agent():
    """创建Agent"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    system_prompt = data.get('system_prompt', '').strip()
    prompt_id = data.get('prompt_id')
    model = data.get('model', 'gpt-4')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2000)
    skills = data.get('skills', [])
    
    if not name:
        return jsonify({'error': 'Agent名称不能为空'}), 400
    
    if not system_prompt and not prompt_id:
        return jsonify({'error': '请设置系统提示词或选择提示词模板'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO agents (name, description, system_prompt, prompt_id, model, temperature, max_tokens, username) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (name, description, system_prompt, prompt_id, model, temperature, max_tokens, username)
                )
                conn.commit()
                agent_id = cursor.lastrowid
                
                if skills:
                    for skill_name in skills:
                        cursor.execute(
                            "INSERT INTO agent_skills (agent_id, skill_name) VALUES (%s, %s)",
                            (agent_id, skill_name)
                        )
                    conn.commit()
                
                return jsonify({
                    'success': True,
                    'agent': {
                        'id': agent_id,
                        'name': name,
                        'description': description,
                        'prompt_id': prompt_id
                    }
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """获取单个Agent"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT a.*, p.name as prompt_name, p.content as prompt_content,
                       GROUP_CONCAT(asl.skill_name ORDER BY asl.skill_name) as skills
                       FROM agents a 
                       LEFT JOIN prompts p ON a.prompt_id = p.id 
                       LEFT JOIN agent_skills asl ON a.id = asl.agent_id
                       WHERE a.id = %s AND a.username = %s
                       GROUP BY a.id""",
                    (agent_id, username)
                )
                agent = cursor.fetchone()
                
                if not agent:
                    return jsonify({'error': 'Agent不存在'}), 404
                
                return jsonify({'agent': agent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/<int:agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """更新Agent"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    system_prompt = data.get('system_prompt', '').strip()
    prompt_id = data.get('prompt_id')
    model = data.get('model', 'gpt-4')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2000)
    skills = data.get('skills', [])
    
    if not name:
        return jsonify({'error': 'Agent名称不能为空'}), 400
    
    if not system_prompt and not prompt_id:
        return jsonify({'error': '请设置系统提示词或选择提示词模板'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE agents SET name = %s, description = %s, system_prompt = %s, prompt_id = %s, 
                       model = %s, temperature = %s, max_tokens = %s, updated_at = CURRENT_TIMESTAMP 
                       WHERE id = %s AND username = %s""",
                    (name, description, system_prompt, prompt_id, model, temperature, max_tokens, agent_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Agent不存在'}), 404
                
                cursor.execute("DELETE FROM agent_skills WHERE agent_id = %s", (agent_id,))
                conn.commit()
                
                if skills:
                    for skill_name in skills:
                        cursor.execute(
                            "INSERT INTO agent_skills (agent_id, skill_name) VALUES (%s, %s)",
                            (agent_id, skill_name)
                        )
                    conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """删除Agent"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM agents WHERE id = %s AND username = %s",
                    (agent_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': 'Agent不存在'}), 404
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 知识库管理 API ====================

@app.route('/api/knowledge-bases', methods=['GET'])
def get_knowledge_bases():
    """获取知识库列表"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    search = request.args.get('search', '')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if search:
                    cursor.execute(
                        """SELECT * FROM knowledge_base 
                           WHERE username = %s AND (name LIKE %s OR description LIKE %s) 
                           ORDER BY updated_at DESC""",
                        (username, f'%{search}%', f'%{search}%')
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM knowledge_base WHERE username = %s ORDER BY updated_at DESC",
                        (username,)
                    )
                kb_list = cursor.fetchall()
                
                for kb in kb_list:
                    for field in ['created_at', 'updated_at']:
                        if kb[field] and isinstance(kb[field], datetime):
                            kb[field] = kb[field].isoformat()
                
                return jsonify(kb_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases', methods=['POST'])
def create_knowledge_base():
    """创建知识库"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': '请输入知识库名称'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO knowledge_base (name, description, username) VALUES (%s, %s, %s)",
                    (name, description, username)
                )
                conn.commit()
                kb_id = cursor.lastrowid
                
                cursor.execute("SELECT * FROM knowledge_base WHERE id = %s", (kb_id,))
                kb = cursor.fetchone()
                
                for field in ['created_at', 'updated_at']:
                    if kb[field] and isinstance(kb[field], datetime):
                        kb[field] = kb[field].isoformat()
                
                return jsonify(kb)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<int:kb_id>', methods=['PUT'])
def update_knowledge_base(kb_id):
    """更新知识库"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': '请输入知识库名称'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE knowledge_base SET name = %s, description = %s WHERE id = %s AND username = %s",
                    (name, description, kb_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': '知识库不存在'}), 404
                
                cursor.execute("SELECT * FROM knowledge_base WHERE id = %s", (kb_id,))
                kb = cursor.fetchone()
                
                for field in ['created_at', 'updated_at']:
                    if kb[field] and isinstance(kb[field], datetime):
                        kb[field] = kb[field].isoformat()
                
                return jsonify(kb)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<int:kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    """删除知识库"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM knowledge_base WHERE id = %s AND username = %s",
                    (kb_id, username)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return jsonify({'error': '知识库不存在'}), 404
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/search', methods=['GET'])
def search_knowledge_bases():
    """搜索知识库"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify([])
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT kb.*, ki.title as item_title, ki.content as item_content
                       FROM knowledge_base kb
                       LEFT JOIN knowledge_item ki ON kb.id = ki.knowledge_base_id
                       WHERE kb.username = %s AND (kb.name LIKE %s OR kb.description LIKE %s OR ki.title LIKE %s OR ki.content LIKE %s)
                       GROUP BY kb.id
                       ORDER BY kb.updated_at DESC""",
                    (username, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
                )
                kb_list = cursor.fetchall()
                
                for kb in kb_list:
                    for field in ['created_at', 'updated_at']:
                        if kb[field] and isinstance(kb[field], datetime):
                            kb[field] = kb[field].isoformat()
                
                return jsonify(kb_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 知识条目 API

@app.route('/api/knowledge-bases/<int:kb_id>/items', methods=['GET'])
def get_knowledge_items(kb_id):
    """获取知识库的知识条目"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT ki.* FROM knowledge_item ki
                       JOIN knowledge_base kb ON ki.knowledge_base_id = kb.id
                       WHERE ki.knowledge_base_id = %s AND kb.username = %s
                       ORDER BY ki.created_at DESC""",
                    (kb_id, username)
                )
                items = cursor.fetchall()
                
                for item in items:
                    for field in ['created_at', 'updated_at']:
                        if item[field] and isinstance(item[field], datetime):
                            item[field] = item[field].isoformat()
                
                return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<int:kb_id>/items', methods=['POST'])
def create_knowledge_item(kb_id):
    """创建知识条目"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    item_type = data.get('type', 'text')
    
    if not title or not content:
        return jsonify({'error': '请输入标题和内容'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE id = %s AND username = %s",
                    (kb_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '知识库不存在'}), 404
                
                cursor.execute(
                    "INSERT INTO knowledge_item (knowledge_base_id, title, content, type) VALUES (%s, %s, %s, %s)",
                    (kb_id, title, content, item_type)
                )
                conn.commit()
                item_id = cursor.lastrowid
                
                cursor.execute("SELECT * FROM knowledge_item WHERE id = %s", (item_id,))
                item = cursor.fetchone()
                
                for field in ['created_at', 'updated_at']:
                    if item[field] and isinstance(item[field], datetime):
                        item[field] = item[field].isoformat()
                
                return jsonify(item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-items/<int:item_id>', methods=['PUT'])
def update_knowledge_item(item_id):
    """更新知识条目"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    item_type = data.get('type', 'text')
    
    if not title or not content:
        return jsonify({'error': '请输入标题和内容'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT ki.id FROM knowledge_item ki
                       JOIN knowledge_base kb ON ki.knowledge_base_id = kb.id
                       WHERE ki.id = %s AND kb.username = %s""",
                    (item_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '知识条目不存在'}), 404
                
                cursor.execute(
                    "UPDATE knowledge_item SET title = %s, content = %s, type = %s WHERE id = %s",
                    (title, content, item_type, item_id)
                )
                conn.commit()
                
                cursor.execute("SELECT * FROM knowledge_item WHERE id = %s", (item_id,))
                item = cursor.fetchone()
                
                for field in ['created_at', 'updated_at']:
                    if item[field] and isinstance(item[field], datetime):
                        item[field] = item[field].isoformat()
                
                return jsonify(item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-items/<int:item_id>', methods=['DELETE'])
def delete_knowledge_item(item_id):
    """删除知识条目"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT ki.id FROM knowledge_item ki
                       JOIN knowledge_base kb ON ki.knowledge_base_id = kb.id
                       WHERE ki.id = %s AND kb.username = %s""",
                    (item_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '知识条目不存在'}), 404
                
                cursor.execute("DELETE FROM knowledge_item WHERE id = %s", (item_id,))
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 知识关系 API

@app.route('/api/knowledge-bases/<int:kb_id>/relations', methods=['GET'])
def get_knowledge_relations(kb_id):
    """获取知识库的知识关系"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT kr.*, ki.title as target_title, ksi.title as source_title
                       FROM knowledge_relation kr
                       JOIN knowledge_base kb ON kr.knowledge_base_id = kb.id
                       LEFT JOIN knowledge_item ki ON kr.target_item_id = ki.id
                       LEFT JOIN knowledge_item ksi ON kr.source_item_id = ksi.id
                       WHERE kr.knowledge_base_id = %s AND kb.username = %s
                       ORDER BY kr.created_at DESC""",
                    (kb_id, username)
                )
                relations = cursor.fetchall()
                
                for rel in relations:
                    if rel['created_at'] and isinstance(rel['created_at'], datetime):
                        rel['created_at'] = rel['created_at'].isoformat()
                
                return jsonify(relations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<int:kb_id>/relations', methods=['POST'])
def create_knowledge_relation(kb_id):
    """创建知识关系"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    source_item_id = data.get('source_item_id')
    target_item_id = data.get('target_item_id')
    relation_type = data.get('relation_type', 'related')
    
    if not source_item_id:
        return jsonify({'error': '请选择源头条目'}), 400
    
    if not target_item_id:
        return jsonify({'error': '请选择目标条目'}), 400
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE id = %s AND username = %s",
                    (kb_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '知识库不存在'}), 404
                
                cursor.execute(
                    "SELECT id FROM knowledge_item WHERE id = %s AND knowledge_base_id = %s",
                    (source_item_id, kb_id)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '源头条目不存在'}), 404
                
                cursor.execute(
                    "SELECT id FROM knowledge_item WHERE id = %s AND knowledge_base_id = %s",
                    (target_item_id, kb_id)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '目标条目不存在'}), 404
                
                cursor.execute(
                    "INSERT INTO knowledge_relation (knowledge_base_id, source_item_id, target_item_id, relation_type) VALUES (%s, %s, %s, %s)",
                    (kb_id, source_item_id, target_item_id, relation_type)
                )
                conn.commit()
                rel_id = cursor.lastrowid
                
                cursor.execute(
                    """SELECT kr.*, ki.title as target_title, ksi.title as source_title
                       FROM knowledge_relation kr
                       LEFT JOIN knowledge_item ki ON kr.target_item_id = ki.id
                       LEFT JOIN knowledge_item ksi ON kr.source_item_id = ksi.id
                       WHERE kr.id = %s""",
                    (rel_id,)
                )
                rel = cursor.fetchone()
                
                if rel['created_at'] and isinstance(rel['created_at'], datetime):
                    rel['created_at'] = rel['created_at'].isoformat()
                
                return jsonify(rel)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-relations/<int:relation_id>', methods=['DELETE'])
def delete_knowledge_relation(relation_id):
    """删除知识关系"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT kr.id FROM knowledge_relation kr
                       JOIN knowledge_base kb ON kr.knowledge_base_id = kb.id
                       WHERE kr.id = %s AND kb.username = %s""",
                    (relation_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '关系不存在'}), 404
                
                cursor.execute("DELETE FROM knowledge_relation WHERE id = %s", (relation_id,))
                conn.commit()
                
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================================================
# 知识图谱 API
# ==================================================

@app.route('/api/knowledge-bases/<int:kb_id>/graph', methods=['GET'])
def get_knowledge_graph(kb_id):
    """获取知识库的图谱数据（节点和边）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    search = request.args.get('search', '')
    relation_types = request.args.get('types', '')
    node_limit = request.args.get('limit', 500, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE id = %s AND username = %s",
                    (kb_id, username)
                )
                kb = cursor.fetchone()
                if not kb:
                    return jsonify({'error': '知识库不存在'}), 404
                
                # 构建节点查询
                nodes_query = "SELECT id, title, content, type FROM knowledge_item WHERE knowledge_base_id = %s"
                nodes_params = [kb_id]
                
                if search:
                    nodes_query += " AND (title LIKE %s OR content LIKE %s)"
                    nodes_params.extend([f'%{search}%', f'%{search}%'])
                
                nodes_query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
                nodes_params.extend([node_limit, offset])
                
                cursor.execute(nodes_query, nodes_params)
                items = cursor.fetchall()
                
                # 构建节点列表
                nodes = []
                node_ids = []
                for item in items:
                    node_id = f"item_{item['id']}"
                    node_ids.append(item['id'])
                    content_preview = item['content'][:100] + '...' if len(item['content']) > 100 else item['content']
                    nodes.append({
                        'id': node_id,
                        'label': item['title'],
                        'type': item['type'],
                        'title': item['title'],
                        'content': content_preview,
                        'fullContent': item['content']
                    })
                
                # 构建边查询
                edges_query = """
                    SELECT kr.id, kr.source_item_id, kr.target_item_id, kr.relation_type,
                           ksi.title as source_title, ki.title as target_title
                    FROM knowledge_relation kr
                    LEFT JOIN knowledge_item ksi ON kr.source_item_id = ksi.id
                    LEFT JOIN knowledge_item ki ON kr.target_item_id = ki.id
                    WHERE kr.knowledge_base_id = %s
                """
                edges_params = [kb_id]
                
                if relation_types:
                    types_list = [t.strip() for t in relation_types.split(',')]
                    placeholders = ', '.join(['%s'] * len(types_list))
                    edges_query += f" AND kr.relation_type IN ({placeholders})"
                    edges_params.extend(types_list)
                
                if search:
                    edges_query += """ AND (
                        ksi.title LIKE %s OR ki.title LIKE %s OR 
                        ksi.content LIKE %s OR ki.content LIKE %s
                    )"""
                    edges_params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
                
                cursor.execute(edges_query, edges_params)
                relations = cursor.fetchall()
                
                # 构建边列表
                edges = []
                relation_type_counts = {}
                
                relation_type_labels = {
                    'related': '相关',
                    'parent': '包含',
                    'child': '从属',
                    'similar': '相似',
                    'tag': '标签'
                }
                
                for rel in relations:
                    if rel['source_item_id'] and rel['target_item_id']:
                        from_id = f"item_{rel['source_item_id']}"
                        to_id = f"item_{rel['target_item_id']}"
                        
                        # 统计关系类型
                        rel_type = rel['relation_type']
                        relation_type_counts[rel_type] = relation_type_counts.get(rel_type, 0) + 1
                        
                        edges.append({
                            'id': f"relation_{rel['id']}",
                            'from': from_id,
                            'to': to_id,
                            'relationType': rel_type,
                            'label': relation_type_labels.get(rel_type, rel_type),
                            'sourceTitle': rel['source_title'],
                            'targetTitle': rel['target_title']
                        })
                
                # 获取统计数据
                cursor.execute(
                    "SELECT COUNT(*) as count FROM knowledge_item WHERE knowledge_base_id = %s",
                    (kb_id,)
                )
                total_nodes = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT COUNT(*) as count FROM knowledge_relation WHERE knowledge_base_id = %s",
                    (kb_id,)
                )
                total_edges = cursor.fetchone()['count']
                
                return jsonify({
                    'nodes': nodes,
                    'edges': edges,
                    'statistics': {
                        'totalNodes': total_nodes,
                        'totalEdges': total_edges,
                        'displayedNodes': len(nodes),
                        'displayedEdges': len(edges),
                        'relationTypes': relation_type_counts
                    }
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<int:kb_id>/graph/export', methods=['POST'])
def export_knowledge_graph(kb_id):
    """导出知识图谱（PNG/SVG）"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    data = request.json
    
    export_format = data.get('format', 'png')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE id = %s AND username = %s",
                    (kb_id, username)
                )
                if not cursor.fetchone():
                    return jsonify({'error': '知识库不存在'}), 404
                
                # 获取完整图谱数据用于导出
                cursor.execute(
                    """SELECT id, title, type FROM knowledge_item WHERE knowledge_base_id = %s""",
                    (kb_id,)
                )
                items = cursor.fetchall()
                
                nodes = [{'id': f"item_{item['id']}", 'label': item['title'], 'type': item['type']} for item in items]
                
                cursor.execute(
                    """SELECT source_item_id, target_item_id, relation_type
                       FROM knowledge_relation WHERE knowledge_base_id = %s""",
                    (kb_id,)
                )
                relations = cursor.fetchall()
                
                edges = []
                for rel in relations:
                    if rel['source_item_id'] and rel['target_item_id']:
                        edges.append({
                            'from': f"item_{rel['source_item_id']}",
                            'to': f"item_{rel['target_item_id']}",
                            'relationType': rel['relation_type']
                        })
                
                return jsonify({
                    'success': True,
                    'format': export_format,
                    'data': {
                        'nodes': nodes,
                        'edges': edges
                    }
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================================================
# Redis 客户端工具
# ==================================================

@app.route('/redis')
def redis_tool():
    """Redis 客户端工具页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('redis.html')

def get_redis_client(host, port, password, db):
    """创建 Redis 客户端连接"""
    if password:
        return redis.Redis(host=host, port=int(port), password=password, db=int(db), decode_responses=True)
    else:
        return redis.Redis(host=host, port=int(port), db=int(db), decode_responses=True)

@app.route('/api/redis/connect', methods=['POST'])
def redis_connect():
    """测试 Redis 连接"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        
        if not host:
            return jsonify({'success': False, 'error': '请输入 Redis 主机地址'})
        
        client = get_redis_client(host, port, password, db)
        client.ping()
        
        return jsonify({'success': True, 'message': '连接成功'})
    except redis.ConnectionError as e:
        return jsonify({'success': False, 'error': f'连接失败: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/keys', methods=['POST'])
def redis_keys():
    """获取 Redis 键列表"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        pattern = data.get('pattern', '*')
        
        client = get_redis_client(host, port, password, db)
        keys = client.keys(pattern)
        
        key_list = []
        for key in keys:
            key_type = client.type(key)
            key_list.append({'key': key, 'type': key_type})
        
        return jsonify({'success': True, 'keys': key_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/get', methods=['POST'])
def redis_get():
    """获取 Redis 值"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        if key_type == 'none':
            return jsonify({'success': False, 'error': '键不存在'})
        
        value = None
        if key_type == 'string':
            value = client.get(key)
        elif key_type == 'list':
            value = client.lrange(key, 0, -1)
        elif key_type == 'set':
            value = list(client.smembers(key))
        elif key_type == 'zset':
            value = client.zrange(key, 0, -1, withscores=True)
        elif key_type == 'hash':
            value = client.hgetall(key)
        
        ttl = client.ttl(key)
        
        return jsonify({
            'success': True,
            'value': value,
            'type': key_type,
            'ttl': ttl
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/hgetall', methods=['POST'])
def redis_hgetall():
    """获取 Hash 所有字段和值"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        if key_type != 'hash':
            return jsonify({'success': False, 'error': f'键类型是 {key_type}，不是 hash'})
        
        value = client.hgetall(key)
        ttl = client.ttl(key)
        
        return jsonify({
            'success': True,
            'value': value,
            'type': 'hash',
            'ttl': ttl
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/lrange', methods=['POST'])
def redis_lrange():
    """获取 List 所有元素"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        if key_type != 'list':
            return jsonify({'success': False, 'error': f'键类型是 {key_type}，不是 list'})
        
        value = client.lrange(key, 0, -1)
        ttl = client.ttl(key)
        
        return jsonify({
            'success': True,
            'value': value,
            'type': 'list',
            'ttl': ttl
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/smembers', methods=['POST'])
def redis_smembers():
    """获取 Set 所有成员"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        if key_type != 'set':
            return jsonify({'success': False, 'error': f'键类型是 {key_type}，不是 set'})
        
        value = client.smembers(key)
        ttl = client.ttl(key)
        
        return jsonify({
            'success': True,
            'value': list(value),
            'type': 'set',
            'ttl': ttl
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/zrange', methods=['POST'])
def redis_zrange():
    """获取 Sorted Set 所有成员"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        if key_type != 'zset':
            return jsonify({'success': False, 'error': f'键类型是 {key_type}，不是 zset'})
        
        value = client.zrange(key, 0, -1, withscores=True)
        ttl = client.ttl(key)
        
        result = [{'member': v[0], 'score': v[1]} for v in value]
        
        return jsonify({
            'success': True,
            'value': result,
            'type': 'zset',
            'ttl': ttl
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/set', methods=['POST'])
def redis_set():
    """设置 Redis 值"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        value = data.get('value', '').strip()
        ttl = data.get('ttl')
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        if value is None or value == '':
            return jsonify({'success': False, 'error': '请输入值'})
        
        client = get_redis_client(host, port, password, db)
        
        if ttl and int(ttl) > 0:
            client.setex(key, int(ttl), value)
        else:
            client.set(key, value)
        
        return jsonify({'success': True, 'message': '设置成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/hset', methods=['POST'])
def redis_hset():
    """设置 Hash 字段"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        field = data.get('field', '').strip()
        value = data.get('value', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        if not field:
            return jsonify({'success': False, 'error': '请输入字段名'})
        if value is None:
            return jsonify({'success': False, 'error': '请输入值'})
        
        client = get_redis_client(host, port, password, db)
        client.hset(key, field, value)
        
        return jsonify({'success': True, 'message': '设置成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/del', methods=['POST'])
@app.route('/api/redis/delete', methods=['POST'])
def redis_del():
    """删除 Redis 键"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        count = client.delete(key)
        
        return jsonify({'success': True, 'message': f'删除了 {count} 个键'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/expire', methods=['POST'])
def redis_expire():
    """设置键的过期时间"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        ttl = data.get('ttl', 0)
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        if not ttl or int(ttl) <= 0:
            return jsonify({'success': False, 'error': '请输入有效的过期时间（秒）'})
        
        client = get_redis_client(host, port, password, db)
        client.expire(key, int(ttl))
        
        return jsonify({'success': True, 'message': f'已设置过期时间 {ttl} 秒'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/persist', methods=['POST'])
def redis_persist():
    """移除键的过期时间"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        client.persist(key)
        
        return jsonify({'success': True, 'message': '已移除过期时间'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/info', methods=['POST'])
def redis_info():
    """获取 Redis 服务器信息"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        
        client = get_redis_client(host, port, password, db)
        info = client.info()
        
        db_key = f'db{db}'
        keyspace = info.get('keyspace', {})
        db_info = keyspace.get(db_key, {})
        
        return jsonify({
            'success': True,
            'info': {
                'version': info.get('redis_version', ''),
                'role': info.get('role', ''),
                'uptime_days': info.get('uptime_in_days', 0),
                'used_memory': info.get('used_memory_human', ''),
                'used_memory_peak': info.get('used_memory_peak_human', ''),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace': keyspace
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/execute', methods=['POST'])
def redis_execute():
    """执行 Redis 命令"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': '请输入命令'})
        
        client = get_redis_client(host, port, password, db)
        
        parts = command.split()
        if not parts:
            return jsonify({'success': False, 'error': '无效的命令'})
        
        cmd = parts[0].upper()
        args = parts[1:]
        
        try:
            result = client.execute_command(cmd, *args)
        except redis.ResponseError as e:
            return jsonify({'success': False, 'error': f'命令执行错误: {str(e)}'})
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/redis/type', methods=['POST'])
def redis_type():
    """获取键的类型"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 6379)
        password = data.get('password', '').strip()
        db = data.get('db', 0)
        key = data.get('key', '').strip()
        
        if not key:
            return jsonify({'success': False, 'error': '请输入键名'})
        
        client = get_redis_client(host, port, password, db)
        key_type = client.type(key)
        
        return jsonify({'success': True, 'type': key_type})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mysql')
def mysql_tool():
    """MySQL 客户端页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('mysql.html')

def get_mysql_connection(host, port, user, password, database=None, timeout=10):
    """获取 MySQL 连接"""
    config = {
        'host': host,
        'port': int(port),
        'user': user,
        'password': password,
        'connect_timeout': int(timeout),
        'cursorclass': pymysql.cursors.DictCursor
    }
    if database:
        config['database'] = database
    return pymysql.connect(**config)

@app.route('/api/mysql/connect', methods=['POST'])
def mysql_connect():
    """连接 MySQL 数据库"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 3306)
        user = data.get('user', 'root').strip()
        password = data.get('password', '')
        database = data.get('database', '').strip()
        timeout = data.get('timeout', 10)
        
        if not host or not user:
            return jsonify({'success': False, 'error': '请输入主机地址和用户名'})
        
        conn = get_mysql_connection(host, port, user, password, database, timeout)
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                databases = [row['Database'] for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'databases': databases
            })
        finally:
            conn.close()
            
    except pymysql.Error as e:
        return jsonify({'success': False, 'error': f'连接失败: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/tables', methods=['POST'])
def mysql_tables():
    """获取数据库表列表"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 3306)
        user = data.get('user', 'root').strip()
        password = data.get('password', '')
        database = data.get('database', '').strip()
        timeout = data.get('timeout', 10)
        
        if not database:
            return jsonify({'success': False, 'error': '请指定数据库'})
        
        conn = get_mysql_connection(host, port, user, password, database, timeout)
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'tables': tables
            })
        finally:
            conn.close()
            
    except pymysql.Error as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/execute', methods=['POST'])
def mysql_execute():
    """执行 SQL 语句"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    try:
        data = request.get_json()
        host = data.get('host', 'localhost').strip()
        port = data.get('port', 3306)
        user = data.get('user', 'root').strip()
        password = data.get('password', '')
        database = data.get('database', '').strip()
        timeout = data.get('timeout', 10)
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({'success': False, 'error': '请输入 SQL 语句'})
        
        if not database:
            return jsonify({'success': False, 'error': '请先选择数据库'})
        
        conn = get_mysql_connection(host, port, user, password, database, timeout)
        
        try:
            import time
            start_time = time.time()
            
            with conn.cursor() as cursor:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    return jsonify({
                        'success': True,
                        'type': 'select',
                        'rows': rows,
                        'rowCount': len(rows),
                        'executionTime': execution_time
                    })
                else:
                    conn.commit()
                    execution_time = int((time.time() - start_time) * 1000)
                    affected = cursor.rowcount
                    
                    return jsonify({
                        'success': True,
                        'type': 'modify',
                        'affectedRows': affected,
                        'executionTime': execution_time,
                        'message': f'执行成功，影响 {affected} 行'
                    })
                    
        except pymysql.Error as e:
            return jsonify({'success': False, 'error': f'SQL 错误: {str(e)}'})
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
    
    # 启动定时任务调度器
    try:
        scheduler.initialize_schedules()
        scheduler.start()
    except Exception as e:
        print(f"⚠️  定时任务调度器启动失败: {e}")
    
    print(f"📝 访问地址: http://localhost:8000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
