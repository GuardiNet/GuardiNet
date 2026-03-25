import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_for_now'
    # DB settings to come
