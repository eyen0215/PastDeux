from flask import Flask, request, jsonify, session
from firebase_admin import credentials, auth, firestore, initialize_app
import os
from dotenv import load_dotenv
from functools import wraps
import pyrebase
from datetime import datetime



class Database:
    def __init__(self):
        load_dotenv()
        self.app = Flask(__name__)
        self.cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        })

        self.firebase_app = initialize_app(self.cred)
        self.db = firestore.client()

        self.firebase_config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASEAUTH_DOMAIN"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "databaseURL": "",
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }

        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()


    # Firestore functions
    def add_user_to_firestore(self, user_data):
        """Add user information to Firestore."""
        users_ref = self.db.collection('users')
        users_ref.document(user_data['uid']).set(user_data)

    def authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            return user
        except Exception as e:
            print("Error authenticating user:", e)
            return None

    def register_user(self, email, password, additional_data):
        """Register new user with email and password."""
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            user_data = {
                "uid": user['localId'],
                "email": email,
                **additional_data
            }
            self.add_user_to_firestore(user_data)
            return user
        except Exception as e:
            print("Error registering user:", e)
            return None
    def add_task(self, user_id, task_data):
        """Add a task to Firestore for a specific user."""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            new_task = tasks_ref.add({
                'type': task_data['type'],
                'description': task_data['description'],
                'due_date': task_data['due_date'],
                'color': task_data['color'],
                'completed': False,
                'created_at': datetime.now().isoformat(),
                'overdue': task_data['overdue']
            })
            # Return the task data with the Firestore document ID
            return {**task_data, 'id': new_task[1].id}
        except Exception as e:
            print("Error adding task:", e)
            return None

    def get_user_tasks(self, user_id):
        """Retrieve all tasks for a specific user."""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            tasks = tasks_ref.stream()
            return [{**task.to_dict(), 'id': task.id} for task in tasks]
        except Exception as e:
            print("Error retrieving tasks:", e)
            return []
    
    def get_calendar(self, user_id):
        """Retrieve all tasks for a specific user."""
        try:
            tasks_ref = self.db.collection('users').document(user_id).collection('tasks')
            tasks = tasks_ref.stream()
            task_dict = [{**task.to_dict(), 'id': task.id} for task in tasks]
            task_list = []
            for task in task_dict:
                if task['completed'] == True or task['overdue'] == True:
                    continue
                due_date, due_time = task['due_date'].split('T')
                task_list.append([task['description'], task['type'], due_date, due_time, user_id, task['id']])
            return task_list
        except Exception as e:
            print("Error retrieving tasks:", e)
            return []

    def update_task(self, user_id, task_id, updates):
        """Update a specific task for a user."""
        try:
            task_ref = self.db.collection('users').document(user_id).collection('tasks').document(task_id)
            task_ref.update(updates)
            return True
        except Exception as e:
            print("Error updating task:", e)
            return False

    def delete_task(self, user_id, task_id):
        """Delete a specific task for a user."""
        try:
            task_ref = self.db.collection('users').document(user_id).collection('tasks').document(task_id)
            task_ref.delete()
            return True
        except Exception as e:
            print("Error deleting task:", e)
            return False
    
    def set_overdue(self, user_id, task_id):
        """Set a task as overdue."""
        return self.update_task(user_id, task_id, {'overdue': True})
    
    def get_user_ids(self):
        """Retrieve all user IDs from Firestore."""
        try:
            users_ref = self.db.collection('users')
            users = users_ref.stream()
            return [user.id for user in users]
        except Exception as e:
            print("Error retrieving user IDs:", e)
            return []
        

