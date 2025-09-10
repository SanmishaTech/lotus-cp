import os
import subprocess
import paramiko
from datetime import datetime
from config import REMOTE_DB, LOCAL_DB, REMOTE_FILES_PATH, LOCAL_FILES_PATH

# --- MySQL Dump from Remote Server ---
def dump_remote_mysql():
    dump_file = f"remote_db_backup_{datetime.now().strftime('%Y%m%d')}.sql"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_DB['host'], username=REMOTE_DB['user'], password=REMOTE_DB['password'])
    dump_cmd = f"mysqldump -u{REMOTE_DB['user']} -p'{REMOTE_DB['password']}' {REMOTE_DB['database']} > /tmp/{dump_file}"
    ssh.exec_command(dump_cmd)
    sftp = ssh.open_sftp()
    sftp.get(f"/tmp/{dump_file}", dump_file)
    sftp.remove(f"/tmp/{dump_file}")
    sftp.close()
    ssh.close()
    return dump_file

# --- Restore to Local MySQL ---
def restore_local_mysql(dump_file):
    cmd = [
        "mysql",
        f"-u{LOCAL_DB['user']}",
        f"-p{LOCAL_DB['password']}",
        LOCAL_DB['database']
    ]
    with open(dump_file, 'rb') as f:
        subprocess.run(cmd, stdin=f)
    os.remove(dump_file)

# --- Sync Files from Remote Server ---
def sync_files():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_DB['host'], username=REMOTE_DB['user'], password=REMOTE_DB['password'])
    sftp = ssh.open_sftp()
    if not os.path.exists(LOCAL_FILES_PATH):
        os.makedirs(LOCAL_FILES_PATH)
    for filename in sftp.listdir(REMOTE_FILES_PATH):
        remote_file = os.path.join(REMOTE_FILES_PATH, filename)
        local_file = os.path.join(LOCAL_FILES_PATH, filename)
        sftp.get(remote_file, local_file)
    sftp.close()
    ssh.close()

if __name__ == "__main__":
    dump_file = dump_remote_mysql()
    restore_local_mysql(dump_file)
    sync_files()
    print("Sync complete. Local machine is now a replica of the server.")
