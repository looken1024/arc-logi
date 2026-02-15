from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for, send_file
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

# 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
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

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

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
    """获取用户的定时任务列表"""
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    username = session['username']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE username = %s ORDER BY created_at DESC",
                    (username,)
                )
                schedules = cursor.fetchall()
                
                # 转换日期格式
                for schedule in schedules:
                    for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
                        if schedule[field] and isinstance(schedule[field], datetime):
                            schedule[field] = schedule[field].isoformat()
                
                return jsonify(schedules)
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
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO schedules (name, description, username, cron, preset, command, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        data['name'],
                        data.get('description', ''),
                        username,
                        data['cron'],
                        data.get('preset', ''),
                        data['command'],
                        data.get('status', 'active')
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

@app.route('/admin')
def admin_page():
    """超级管理员页面"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/api/admin/opencode', methods=['POST'])
def admin_opencode():
    """远程开发 - 执行 opencode 命令"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': '命令不能为空'})
        
        result = subprocess.run(
            ['bash', '-c', f'cd /home/yangkai/github/arc-logi/chat && opencode run "{command}"'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout
        if result.stderr:
            output += '\n' + result.stderr
        
        return jsonify({
            'success': True,
            'output': output,
            'returncode': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '命令执行超时'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/restart', methods=['POST'])
def admin_restart():
    """系统更新 - 停止应用"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ctl_script = os.path.join(script_dir, 'ctl.sh')
        
        if not os.path.exists(ctl_script):
            return jsonify({'success': False, 'error': '重启脚本不存在'})
        
        def do_restart():
            import time
            time.sleep(2)
            subprocess.Popen(
                ['bash', ctl_script, 'stop'],
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        thread = threading.Thread(target=do_restart)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'output': '停止命令已发送，服务即将停止。',
            'returncode': 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
    
    print(f"📝 访问地址: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
