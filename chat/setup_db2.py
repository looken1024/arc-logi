#!/usr/bin/env python3
import pymysql
import sys
import os

try:
    # Connect via socket
    conn = pymysql.connect(
        host='127.0.0.1', 
        user='root',
        password='root123',
        port=3306,
        unix_socket='/tmp/mysql.sock'
    )
    print('Connected to MySQL!')
    cursor = conn.cursor()
    
    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS arc_logi_chat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute('SHOW DATABASES')
    dbs = [x[0] for x in cursor.fetchall()]
    print('Databases:', dbs)
    
    conn.close()
    print('Database setup complete!')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)