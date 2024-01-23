# -*- coding: utf-8 -*-
"""APITest.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qNgnxfGhEv_85yTxN0FnXi_DRvIXacS9
"""
import os

from flask import Flask, jsonify, request



app = Flask(__name__)

todo_tasks = []
current_task_id = 0 # A global variable to store the current task id



@app.route("/tasks", methods=['GET', 'POST'])
def manage_tasks():
    global current_task_id # Use the global variable
    if request.method == 'GET':
        return jsonify(todo_tasks)
    elif request.method == 'POST':
        task = request.json.get('task', '')
        if task:
            current_task_id += 1 # Increment the current task id
            todo_tasks.append({'id': current_task_id, 'task': task, 'status': 'pending'}) # Add the task with the id
            return jsonify({'message': 'Task added', 'id': current_task_id}), 201 # Return the id of the added task
        else:
            return jsonify({'message': 'Task is required'}), 400


@app.route("/tasks/<int:id>", methods=['PUT', 'DELETE'])
def modify_task(id):
    task = [t for t in todo_tasks if t['id'] == id] # Find the task by id
    if len(task) == 0: # If no task is found, return an error message and status code
        return jsonify({'message': 'Task not found'}), 404
    if request.method == 'PUT': # If the request method is PUT, update the task
        task[0]['task'] = request.json.get('task', task[0]['task']) # Update the task content
        task[0]['status'] = request.json.get('status', task[0]['status']) # Update the task status
        return jsonify({'message': 'Task updated'}), 200
    elif request.method == 'DELETE': # If the request method is DELETE, remove the task
        todo_tasks.remove(task[0]) # Remove the task from the list
        return jsonify({'message': 'Task deleted'}), 200


if __name__ == "__main__":
      app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) #for deploy on vercel



