import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import Config
from database.db import db, init_db

def setup_database():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Creating all database tables in SQLite...")
        init_db()
        print("Database tables initialized successfully!")

if __name__ == '__main__':
    setup_database()
