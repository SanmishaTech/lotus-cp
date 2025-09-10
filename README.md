# Python Project: Daily MySQL & File Sync

## Project Overview
This project automates the daily copying of a MySQL database and associated files from a remote server to a local machine, ensuring the local environment is an exact replica of the software hosted online.

## Features
- Daily backup of MySQL database from server to local machine
- Daily sync of files attached in the software from server to local machine
- Ensures local machine mirrors the server setup

## Setup Instructions
1. Clone this repository to your local machine.
2. Install required Python dependencies (see requirements.txt).
3. Configure server and local credentials in `config.py`.
4. Run the main script manually or set up a cron job for daily execution.

## Usage
- To run the sync manually:
  ```bash
  python main.py
  ```
- To automate daily sync, add a cron job (see below).

## Cron Job Example
```
0 2 * * * /usr/bin/python3 /path/to/project/main.py
```

## Notes
- Ensure you have network access to the remote server.
- MySQL credentials and file paths must be correctly set in `config.py`.
- For large file sets, consider using rsync for efficiency.

---

For questions or issues, contact the project maintainer.
