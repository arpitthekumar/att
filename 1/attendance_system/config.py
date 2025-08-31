import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///attendance.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
