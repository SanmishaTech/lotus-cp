# Python Project: Daily MySQL & File Sync

## Project Overview
This project automates the daily copying of a remote MySQL database (via direct network mysqldump) and associated files from an FTP server to a local machine, ensuring the local environment is an exact replica (data + files) of the software hosted online.

## Features
- Daily backup of remote MySQL database to local machine using mysqldump
- FTP file retrieval (supports optional extension filtering)
 - Optional recursive FTP directory traversal (enable with FTP_RECURSIVE=true)
- Logs progress and errors
- Ensures local machine mirrors the server's data & file assets

## Setup Instructions
1. Clone this repository to your local machine.
2. Install required Python dependencies (see requirements.txt).
3. Copy `.env.example` to `.env` and fill in credentials (remote DB, local DB, FTP server, paths).
4. Run the main script manually or set up a cron job for daily execution.

## Usage
- To run the sync manually:
  ```bash
  python main.py
  ```
- To automate daily sync, add a cron job (see below).

## Cron Job Example
Two options:

1) Using the provided wrapper (recommended):
   - Make it executable once:
     - chmod +x ./scripts/run_sync.sh
   - Edit your crontab and add (runs at 6pm daily):
```
0 18 * * * /bin/bash -lc '/home/administrator/lotus-cp/scripts/run_sync.sh'
```

2) Direct Python call (ensure venv + PATH are correct):
```
0 18 * * * cd /home/administrator/lotus-cp && . .venv/bin/activate && python main.py >> logs/sync_$(date +\%F).log 2>&1
```

## Notes
- Ensure outbound access to the remote MySQL host and FTP host.
- Ensure `mysqldump` and `mysql` client binaries are installed and in PATH.
- When running under cron, the environment is minimal; use the wrapper script to set PATH, working directory, venv, and logging.
- Use passive FTP if behind firewalls (default is passive=true).
- For very large file sets or directory trees, extend the script for recursive FTP (current version handles a single directory flat list).

## Environment Variables (.env)
Key variables (see `.env.example` for full list):
- REMOTE_DB_HOST / REMOTE_DB_PORT / REMOTE_DB_USER / REMOTE_DB_PASSWORD / REMOTE_DB_NAME
- LOCAL_DB_HOST / LOCAL_DB_PORT / LOCAL_DB_USER / LOCAL_DB_PASSWORD / LOCAL_DB_NAME
- REMOTE_FTP_HOST / REMOTE_FTP_USER / REMOTE_FTP_PASSWORD / REMOTE_FTP_PASSIVE
- REMOTE_FILES_PATH / LOCAL_FILES_PATH
- FILTER_EXTENSIONS
 - FTP_RECURSIVE
 - FTP_RECENT_ONLY / FTP_RECENT_WINDOW_HOURS

If FILTER_EXTENSIONS is set (e.g. `.jpg,.png`), only those files are downloaded. Set `FTP_RECURSIVE=true` to traverse subdirectories; otherwise only the top-level files are downloaded and folders are skipped.

Recent-only mode: set `FTP_RECENT_ONLY=true` and optionally `FTP_RECENT_WINDOW_HOURS=24` (default 24) to download only files whose FTP MDTM timestamp is within the last N hours. If MDTM isn't supported for a file, it is downloaded to avoid missing updates.

---

For questions or issues, contact the project maintainer.
