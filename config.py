import os
from dotenv import load_dotenv

load_dotenv()

# Configuration for server and local paths

REMOTE_DB = {
    'host': os.getenv('REMOTE_DB_HOST'),
    'user': os.getenv('REMOTE_DB_USER'),
    'password': os.getenv('REMOTE_DB_PASSWORD'),
    'database': os.getenv('REMOTE_DB_NAME')
}

LOCAL_DB = {
    'host': os.getenv('LOCAL_DB_HOST', 'localhost'),
    'user': os.getenv('LOCAL_DB_USER'),
    'password': os.getenv('LOCAL_DB_PASSWORD'),
    'database': os.getenv('LOCAL_DB_NAME')
}

REMOTE_FILES_PATH = os.getenv('REMOTE_FILES_PATH')
LOCAL_FILES_PATH = os.getenv('LOCAL_FILES_PATH')

# Add any other configuration as needed
