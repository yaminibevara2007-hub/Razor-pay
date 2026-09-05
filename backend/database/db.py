from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db():
    # Import models so tables are registered with SQLAlchemy
    from database import models
    db.create_all()
