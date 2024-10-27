from flask import Flask, request, jsonify
from firebase_admin import credentials, auth, firestore, initialize_app
import os
from dotenv import load_dotenv
from functools import wraps
import pyrebase


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

