from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.environ.get("MONGODB_URI"))
        self.db = self.client["telegram_bot"]  # Replace "telegram_bot" with your desired database name
        self.users = self.db["users"]
        self.chats = self.db["chats"]
        self.files = self.db["files"]

    # User management methods
    def register_user(self, chat_id, first_name, username):
        user_data = {
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None  # Initially None, update when received
        }
        self.users.update_one({"chat_id": chat_id}, {"$set": user_data}, upsert=True)

    def update_phone_number(self, chat_id, phone_number):
        self.users.update_one({"chat_id": chat_id}, {"$set": {"phone_number": phone_number}})

    def get_user(self, chat_id):
        return self.users.find_one({"chat_id": chat_id})

    # Chat history methods
    def save_chat_message(self, chat_id, user_message, bot_response):
        chat_data = {
            "chat_id": chat_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.now()
        }
        self.chats.insert_one(chat_data)

    # File management methods
    def save_file_metadata(self, chat_id, file_id, file_name, description):
        file_data = {
            "chat_id": chat_id,
            "file_id": file_id,
            "file_name": file_name,
            "description": description,
            "timestamp": datetime.now()
        }
        self.files.insert_one(file_data)