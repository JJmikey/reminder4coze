# app.py
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import parser


import os 
import json
import requests

from flask import Flask, jsonify, request
import logging

import firebase_admin
from firebase_admin import credentials, db


# Load the credentials from environment variable
firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
if firebase_service_account is not None:
    service_account_info = json.loads(firebase_service_account)
else:
    print("'FIREBASE_SERVICE_ACCOUNT' is not set or empty")
    # handle this error appropriately...


# Initialize the Firebase application with Firebase database URL
firebase_admin.initialize_app(credentials.Certificate(service_account_info), {'databaseURL': 'https://reminderapi-92cb1-default-rtdb.asia-southeast1.firebasedatabase.app//'})

# 从环境变量获取 Slack webhook URL
webhook_url = os.getenv('SLACK_WEBHOOK_URL')

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

# Define your scheduled job function
def scheduled_job():
    # Scheduler job to check for due reminders, etc.
    ref = db.reference("/")
    now = datetime.now(pytz.utc)

    # Read from Firebase
    tasks = ref.get()  
    if tasks:
        for task_id, task_details in tasks.items():
            if 'reminder_time' in task_details:
                # Parse the reminder time
                reminder_time = datetime.fromisoformat(task_details['reminder_time'])
                if reminder_time <= now:
                    # If the reminder time has passed, send a reminder
                    send_reminder(task_details['task'])
                    # Delete the task from Firebase or mark as completed
                    ref.child(str(task_id)).delete()  # This will completely remove the task

def send_reminder(task_description):
    # 要发送的消息内容
    message = f"Reminder for task: {task_description}"

    # 建立请求的数据载体
    slack_data = {'text': message}

    # 发送 POST 请求到 Slack webhook URL
    response = requests.post(
        webhook_url, json=slack_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise ValueError(f"Request to slack returned an error {response.status_code}, the response is:\n{response.text}")


# 这一段代码移到app开始之前
if __name__ == '__main__':
    # Initialize APScheduler only if running this file as the main program
    scheduler = BackgroundScheduler(daemon=True)
    # your scheduled jobs here
    scheduler.add_job(scheduled_job, 'interval', minutes=1)
    scheduler.start()

    # Properly handle scheduler shutdown
    atexit.register(lambda: scheduler.shutdown(wait=False))

    # Start Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel

@app.route("/task", methods=['GET', 'POST'])
def manage_tasks():
    ref = db.reference("/")
    if request.method == 'GET':
        # Read from Firebase
        todo_tasks = ref.get()
        return jsonify(todo_tasks)
    elif request.method == 'POST':
        task = request.json.get('task', '')
        reminder_time_input = request.json.get('reminder_time', '')

        # Parse natural language date/time input to a datetime object
        try:
            reminder_time = parser.parse(reminder_time_input)
        except ValueError:
            return jsonify({'message': 'Invalid date/time format'}), 400
            
        if task:
            # Get current_task_id from Firebase and increment it
            current_task_id = ref.child("current_task_id").get()
            if current_task_id is None:
                # If it doesn't exist, start it at 1
                current_task_id = 1
            else:
                current_task_id += 1

            reminder_time = request.json.get('reminder_time', '')

            # Ensure reminder_time is valid
            try:
                # you could allow different formats, here I expect it to be ISO8601
                reminder_time = datetime.fromisoformat(reminder_time)
            except ValueError:
                return jsonify({'message': 'Invalid reminder time format. Use ISO8601.'}), 400
        
            # Write to Firebase
            ref.child("{}".format(current_task_id)).set({
                'id': current_task_id, 
                'task': task, 
                'reminder_time': reminder_time.isoformat()  # Store as string in ISO format
            })
            ref.child("current_task_id").set(current_task_id)
            send_reminder(task) # test webhook message function
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201
            
        else:
            return jsonify({'message': 'Task is required'}), 400

