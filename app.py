#This is a simple Python CGI implementation of the task logger API. 
#You will refactor this source code to a more modern Flask based approach and run it on your server. 
#This source code contains a common security venerability. Please try to identify and resolve this during refactoring.


#!/usr/bin/python3
from flask import Flask, request, jsonify, abort
import os
import pymysql
import urllib.parse

app = Flask(__name__)

# Database connection parameters - update as needed
DB_USER = os.getenv('DB_USER') or 'root'
DB_PSWD = os.getenv('DB_PSWD') or 'password'
DB_NAME = os.getenv('DB_NAME') or 'task_logger'
DB_HOST = os.getenv('DB_HOST') or '127.0.0.1'
DB_SOCKET = os.getenv('DB_SOCKET') or None

def get_db_connection():
    if DB_SOCKET is None:
        return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PSWD, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)
    else:
        return pymysql.connect(unix_socket=DB_SOCKET, user=DB_USER, password=DB_PSWD, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)

# Helper function to validate title length
def is_valid_title(title):
    return 6 <= len(title) <= 255

@app.route('/', methods=['POST', 'GET', 'PUT', 'DELETE'])
def tasks():
    if request.method == 'POST':
        # Extract the value after the question mark
        full_path = request.full_path
        title = full_path.split('?')[1] if '?' in full_path else None
        
        if title and is_valid_title(title):
            title = title.replace('+', ' ')
            try:
                with get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
                        connection.commit()
                        task_id = cursor.lastrowid
                        cursor.execute("SELECT id, title, DATE_FORMAT(created, '%Y-%m-%d %H:%i:%s') as created FROM tasks WHERE id = LAST_INSERT_ID()")
                        new_task = cursor.fetchone()
                        return jsonify(new_task), 201
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error="Invalid title"), 400

    elif request.method == 'GET':
        full_path = request.full_path
        task_id = full_path.split('?')[1] if '?' in full_path else None
        if task_id:
            try:
                with get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT id, title, DATE_FORMAT(created, '%Y-%m-%d %H:%i') as created FROM tasks WHERE id = %s", (task_id,))
                        task = cursor.fetchone()
                if task:
                    return jsonify(task), 200
                else:
                    return jsonify(error="Task not found"), 404
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            try:
                with get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT id, title, DATE_FORMAT(created, '%Y-%m-%d %H:%i') as created FROM tasks")
                        tasks = cursor.fetchall()
                return jsonify(tasks), 200
            except Exception as e:
                return jsonify(error=str(e)), 500
    
    elif request.method == 'PUT':
        full_path = request.full_path
        task = full_path.split('?')[1] if '?' in full_path else None
        task_i = task.split('/') if task else None
        task_id = task_i[0] if task_i else None
        new_title = task_i[1] if task_i else None
        if new_title and is_valid_title(new_title):
            try:
                with get_db_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE tasks SET title = %s WHERE id = %s", (new_title, task_id))
                        connection.commit()
                        return jsonify(message="Task updated successfully"), 200
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error="Invalid title"), 400

    elif request.method == 'DELETE':
        full_path = request.full_path
        task_id = full_path.split('?')[1] if '?' in full_path else None
        
        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                    connection.commit()
            return jsonify(message="Task deleted successfully"), 200
        except Exception as e:
            return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
