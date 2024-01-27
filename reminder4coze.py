# app.py
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler



import os 
import json

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



app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

# Define your scheduled job function
def scheduled_job():
    # Scheduler job to check for due reminders, etc.
    pass

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
                'status': 'pending',
                'reminder_time': reminder_time.isoformat()  # Store as string in ISO format
            })
            ref.child("current_task_id").set(current_task_id)
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201
        else:
            return jsonify({'message': 'Task is required'}), 400

