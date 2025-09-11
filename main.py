import os
import subprocess
import logging
import sys
from datetime import datetime, timezone
from ftplib import FTP
from config import (
    REMOTE_DB,
    LOCAL_DB,
    REMOTE_FILES_PATH,
    LOCAL_FILES_PATH,
    REMOTE_FTP,
    FILTER_EXTENSIONS,
    RECURSIVE_FTP,
    RECENT_ONLY,
    RECENT_WINDOW_HOURS,
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

    def is_directory(ftp_conn: FTP, name: str) -> bool:
        current = ftp_conn.pwd()
        try:
            ftp_conn.cwd(name)
            ftp_conn.cwd(current)
            return True
        except Exception:
            return False

    def get_mdtm_datetime(ftp_conn: FTP, name: str):
        """Return UTC datetime for file via MDTM or None if unsupported."""
        try:
            resp = ftp_conn.sendcmd(f"MDTM {name}")  # format: '213 YYYYMMDDHHMMSS'
            if not resp.startswith('213 '):
                return None
            ts = resp.split()[1].strip()
        # MDTM timestamps are in UTC; return a timezone-aware datetime
        return datetime.strptime(ts, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
        except Exception:
            return None

    # Use timezone-aware UTC now to avoid deprecation warnings
    recent_cutoff = datetime.now(timezone.utc)

    def is_recent(ftp_conn: FTP, name: str) -> bool:
        if not RECENT_ONLY:
            return True
        mdtm = get_mdtm_datetime(ftp_conn, name)
        if mdtm is None:
            # If MDTM unsupported, default to downloading to avoid missing updates
            return True
        delta_hours = (recent_cutoff - mdtm).total_seconds() / 3600.0
        return delta_hours <= RECENT_WINDOW_HOURS

    def get_size(ftp_conn: FTP, name: str):
        try:
            return ftp_conn.size(name)
        except Exception:
            return None

    def make_progress_writer(file_handle, total_size, label):
        bytes_written = {'n': 0}
        last_pct = {'p': -1}

        def cb(data: bytes):
            file_handle.write(data)
            bytes_written['n'] += len(data)
            if total_size and total_size > 0:
                pct = int(bytes_written['n'] * 100 / total_size)
                if pct != last_pct['p']:
                    last_pct['p'] = pct
                    sys.stdout.write(f"\rDownloading {label}: {pct}% ({bytes_written['n']}/{total_size} bytes)")
                    sys.stdout.flush()
            else:
                # Unknown total size; print in MB every ~1MB
                if bytes_written['n'] % (1024 * 1024) < len(data):
                    mb = bytes_written['n'] / (1024 * 1024)
                    sys.stdout.write(f"\rDownloading {label}: {mb:.1f} MiB")
                    sys.stdout.flush()
        return cb, bytes_written, last_pct

    def finish_progress(label):
        sys.stdout.write(f"\rDownloading {label}: 100%\n")
        sys.stdout.flush()

    def download_dir(ftp_conn: FTP, remote_dir: str, local_dir: str):
        ftp_conn.cwd(remote_dir)
        os.makedirs(local_dir, exist_ok=True)
        for entry in ftp_conn.nlst():
            if entry in ('.', '..'):
                continue
            if is_directory(ftp_conn, entry):
                if RECURSIVE_FTP:
                    download_dir(ftp_conn, entry, os.path.join(local_dir, entry))
                else:
                    logging.debug('Skipping directory (recursion disabled): %s/%s', remote_dir, entry)
            else:
                if not should_download(entry):
                    continue
                if not is_recent(ftp_conn, entry):
                    continue
                local_target = os.path.join(local_dir, entry)
                label = f"{remote_dir}/{entry}"
                size = get_size(ftp_conn, entry)
                logging.info('Downloading %s -> %s (%s bytes)', label, local_target, size if size is not None else 'unknown')
                with open(local_target, 'wb') as f:
                    cb, *_ = make_progress_writer(f, size, label)
                    ftp_conn.retrbinary(f'RETR {entry}', cb)
                finish_progress(label)
        ftp_conn.cwd('..')

    logging.info('Connecting to FTP %s', REMOTE_FTP['host'])
    ftp = FTP()
    ftp.connect(REMOTE_FTP['host'])
    ftp.login(REMOTE_FTP['user'], REMOTE_FTP['password'])
    if REMOTE_FTP['passive']:
        ftp.set_pasv(True)
    ftp.cwd(REMOTE_FILES_PATH)
    for name in ftp.nlst():
        if name in ('.', '..'):
            continue
        if is_directory(ftp, name):
            if RECURSIVE_FTP:
                download_dir(ftp, name, os.path.join(LOCAL_FILES_PATH, name))
            else:
                logging.debug('Skipping directory: %s', name)
            continue
        if not should_download(name):
            continue
        if not is_recent(ftp, name):
            continue
        local_target = os.path.join(LOCAL_FILES_PATH, name)
        size = get_size(ftp, name)
        logging.info('Downloading %s -> %s (%s bytes)', name, local_target, size if size is not None else 'unknown')
        with open(local_target, 'wb') as f:
            cb, *_ = make_progress_writer(f, size, name)
            ftp.retrbinary(f'RETR {name}', cb)
        finish_progress(name)
    ftp.quit()
    logging.info('FTP file sync complete')

def main():
    dump_file = run_mysqldump()
    restore_local_mysql(dump_file)
    sync_files()
    logging.info('All tasks complete.')

if __name__ == '__main__':
    main()
