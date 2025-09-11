import os
import subprocess
import logging
from datetime import datetime
from ftplib import FTP
from config import (
    REMOTE_DB,
    LOCAL_DB,
    REMOTE_FILES_PATH,
    LOCAL_FILES_PATH,
    REMOTE_FTP,
    FILTER_EXTENSIONS,
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def run_mysqldump():
    """Run mysqldump directly against remote MySQL host (needs network access & privileges)."""
    dump_file = f"remote_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    cmd = [
        'mysqldump',
        f"-h{REMOTE_DB['host']}",
        f"-P{REMOTE_DB['port']}",
        f"-u{REMOTE_DB['user']}",
        f"-p{REMOTE_DB['password']}",
        '--single-transaction',
        '--quick',
        '--routines',
        '--events',
        REMOTE_DB['database']
    ]
    logging.info('Starting mysqldump from remote host %s', REMOTE_DB['host'])
    with open(dump_file, 'wb') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error('mysqldump failed: %s', result.stderr.decode())
        raise RuntimeError('mysqldump failed')
    logging.info('mysqldump complete: %s', dump_file)
    return dump_file

# --- Restore to Local MySQL ---
def restore_local_mysql(dump_file):
    cmd = [
        'mysql',
        f"-h{LOCAL_DB['host']}",
        f"-P{LOCAL_DB['port']}",
        f"-u{LOCAL_DB['user']}",
        f"-p{LOCAL_DB['password']}",
        LOCAL_DB['database']
    ]
    logging.info('Restoring dump into local database %s', LOCAL_DB['database'])
    with open(dump_file, 'rb') as f:
        result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error('mysql restore failed: %s', result.stderr.decode())
        raise RuntimeError('mysql restore failed')
    logging.info('Restore complete')
    os.remove(dump_file)

# --- Sync Files from Remote Server ---
def sync_files():
    if not REMOTE_FTP['host']:
        logging.warning('REMOTE_FTP_HOST not set; skipping file sync')
        return
    if not os.path.exists(LOCAL_FILES_PATH):
        os.makedirs(LOCAL_FILES_PATH, exist_ok=True)

    def should_download(name: str) -> bool:
        if not FILTER_EXTENSIONS:
            return True
        return any(name.lower().endswith(ext.lower()) for ext in FILTER_EXTENSIONS)

    logging.info('Connecting to FTP %s', REMOTE_FTP['host'])
    ftp = FTP()
    ftp.connect(REMOTE_FTP['host'])
    ftp.login(REMOTE_FTP['user'], REMOTE_FTP['password'])
    if REMOTE_FTP['passive']:
        ftp.set_pasv(True)
    ftp.cwd(REMOTE_FILES_PATH)
    names = ftp.nlst()
    for name in names:
        if name in ('.', '..'):
            continue
        if not should_download(name):
            continue
        local_target = os.path.join(LOCAL_FILES_PATH, name)
        logging.info('Downloading %s -> %s', name, local_target)
        with open(local_target, 'wb') as f:
            ftp.retrbinary(f'RETR {name}', f.write)
    ftp.quit()
    logging.info('FTP file sync complete')

def main():
    dump_file = run_mysqldump()
    restore_local_mysql(dump_file)
    sync_files()
    logging.info('All tasks complete.')

if __name__ == '__main__':
    main()
