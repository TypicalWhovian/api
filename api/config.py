import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE = os.environ.get('DATABASE')
    TEST_DATABASE = os.environ.get('TEST_DATABASE')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
