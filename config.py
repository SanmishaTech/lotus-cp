import os
try:
    from dotenv import load_dotenv  # provided by python-dotenv
except ImportError:  # graceful fallback if dependency not installed
    print("[WARN] python-dotenv not installed. Install with: pip install python-dotenv")
    def load_dotenv(path: str | None = None, **_: dict):
        """Minimal .env loader fallback. Supports KEY=VALUE lines, ignores comments."""
        env_path = path or os.path.join(os.path.dirname(__file__), '.env')
        if not os.path.exists(env_path):
            return False
        try:
            with open(env_path, 'r') as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Do not override existing env
                    if key and key not in os.environ:
                        os.environ[key] = val
            return True
        except Exception:
            return False

load_dotenv()

# Remote MySQL configuration (accessed directly over network)
REMOTE_DB = {
    'host': os.getenv('REMOTE_DB_HOST'),
    'user': os.getenv('REMOTE_DB_USER'),
    'password': os.getenv('REMOTE_DB_PASSWORD'),
    'database': os.getenv('REMOTE_DB_NAME'),
    'port': int(os.getenv('REMOTE_DB_PORT', '3306'))
}

# Local MySQL target database
LOCAL_DB = {
    'host': os.getenv('LOCAL_DB_HOST', 'localhost'),
    'user': os.getenv('LOCAL_DB_USER'),
    'password': os.getenv('LOCAL_DB_PASSWORD'),
    'database': os.getenv('LOCAL_DB_NAME'),
    'port': int(os.getenv('LOCAL_DB_PORT', '3306'))
}

# File sync paths
REMOTE_FILES_PATH = os.getenv('REMOTE_FILES_PATH', '/')
LOCAL_FILES_PATH = os.getenv('LOCAL_FILES_PATH', './synced_files')

# FTP server credentials
REMOTE_FTP = {
    'host': os.getenv('REMOTE_FTP_HOST'),
    'user': os.getenv('REMOTE_FTP_USER'),
    'password': os.getenv('REMOTE_FTP_PASSWORD'),
    'passive': os.getenv('REMOTE_FTP_PASSIVE', 'true').lower() == 'true'
}

# Optional: limit download to certain extensions (comma-separated in env)
FILTER_EXTENSIONS = [ext.strip() for ext in os.getenv('FILTER_EXTENSIONS', '').split(',') if ext.strip()]

# Recursive FTP sync toggle
RECURSIVE_FTP = os.getenv('FTP_RECURSIVE', 'false').lower() == 'true'

# Recent file filtering
RECENT_ONLY = os.getenv('FTP_RECENT_ONLY', 'false').lower() == 'true'
RECENT_WINDOW_HOURS = int(os.getenv('FTP_RECENT_WINDOW_HOURS', '24'))

# Performance tuning
FTP_MAX_WORKERS = int(os.getenv('FTP_MAX_WORKERS', '4'))
FTP_TIMEOUT = int(os.getenv('FTP_TIMEOUT', '60'))  # seconds
FTP_USE_MLSD = os.getenv('FTP_USE_MLSD', 'true').lower() == 'true'
FTP_SKIP_UNCHANGED = os.getenv('FTP_SKIP_UNCHANGED', 'true').lower() == 'true'

# Add any other configuration as needed
