import threading
import time
import uuid
from datetime import datetime, timedelta
from croniter import croniter
import pymysql
import os
from contextlib import contextmanager

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

def execute_schedule_command(schedule_id, execution_id, command):
    """执行定时任务命令"""
    from contextlib import contextmanager
    
    output = ""
    error_message = None
    
    try:
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600
        )
        
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        
        status = 'completed' if result.returncode == 0 else 'failed'
        if result.returncode != 0:
            error_message = f"Exit code: {result.returncode}"
    except subprocess.TimeoutExpired:
        error_message = "执行超时（超过1小时）"
        status = 'failed'
    except Exception as e:
        error_message = str(e)
        status = 'failed'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE schedule_executions SET status = %s, output = %s, error_message = %s, completed_at = CURRENT_TIMESTAMP "
                    "WHERE execution_id = %s",
                    (status, output, error_message, execution_id)
                )
                conn.commit()
    except Exception as e:
        print(f"更新执行记录失败: {e}")

def calculate_next_run_time(cron_str, from_time=None):
    """根据 cron 表达式计算下次执行时间"""
    if from_time is None:
        from_time = datetime.now()
    
    try:
        cron = croniter(cron_str, from_time)
        return cron.get_next(datetime)
    except Exception as e:
        print(f"Cron 解析错误: {e}")
        return None

class ScheduleScheduler:
    """定时任务调度器"""
    
    def __init__(self, check_interval=60):
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
    def start(self):
        """启动调度器"""
        with self.lock:
            if self.running:
                print("调度器已在运行中")
                return
            
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("✅ 定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
            print("⏹️ 定时任务调度器已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        while self.running:
            try:
                self._check_and_execute_schedules()
            except Exception as e:
                print(f"调度器执行错误: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_and_execute_schedules(self):
        """检查并执行到期的定时任务"""
        now = datetime.now()
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, name, command, username, cron, next_run_at 
                           FROM schedules 
                           WHERE status = 'active' 
                           AND (next_run_at IS NULL OR next_run_at <= %s)""",
                        (now,)
                    )
                    schedules = cursor.fetchall()
                    
                    for schedule in schedules:
                        self._execute_schedule(schedule)
                        
        except Exception as e:
            print(f"检查定时任务失败: {e}")
    
    def _execute_schedule(self, schedule):
        """执行单个定时任务"""
        schedule_id = schedule['id']
        execution_id = str(uuid.uuid4())
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO schedule_executions (schedule_id, username, execution_id, status) "
                        "VALUES (%s, %s, %s, 'running')",
                        (schedule_id, schedule['username'], execution_id)
                    )
                    
                    next_run = calculate_next_run_time(schedule['cron'])
                    cursor.execute(
                        "UPDATE schedules SET last_run_at = CURRENT_TIMESTAMP, next_run_at = %s, updated_at = CURRENT_TIMESTAMP "
                        "WHERE id = %s",
                        (next_run, schedule_id)
                    )
                    
                    conn.commit()
            
            thread = threading.Thread(
                target=execute_schedule_command,
                args=(schedule_id, execution_id, schedule['command']),
                daemon=True
            )
            thread.start()
            
            print(f"🕐 定时任务已执行: {schedule['name']} (ID: {schedule_id})")
            
        except Exception as e:
            print(f"执行定时任务失败: {e}")
    
    def update_schedule_next_run(self, schedule_id, cron_str):
        """更新定时任务的下次执行时间"""
        next_run = calculate_next_run_time(cron_str)
        if next_run:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE schedules SET next_run_at = %s WHERE id = %s",
                            (next_run, schedule_id)
                        )
                        conn.commit()
            except Exception as e:
                print(f"更新下次执行时间失败: {e}")
    
    def initialize_schedules(self):
        """初始化所有活跃定时任务的下次执行时间"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, cron FROM schedules WHERE status = 'active' AND next_run_at IS NULL"""
                    )
                    schedules = cursor.fetchall()
                    
                    for schedule in schedules:
                        next_run = calculate_next_run_time(schedule['cron'])
                        if next_run:
                            cursor.execute(
                                "UPDATE schedules SET next_run_at = %s WHERE id = %s",
                                (next_run, schedule['id'])
                            )
                    
                    conn.commit()
                    print(f"✅ 已初始化 {len(schedules)} 个定时任务的下次执行时间")
                    
        except Exception as e:
            print(f"初始化定时任务失败: {e}")

scheduler = ScheduleScheduler(check_interval=60)
