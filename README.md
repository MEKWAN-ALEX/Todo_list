# To-Do List (Streamlit)

A simple Streamlit To-Do list web application that stores tasks in a local SQLite database, shows desktop notifications when tasks are due or when a configured notify time is reached, and includes a background scheduler to check deadlines.

This repository contains:

- `todolist_streamlit.py` — main Streamlit application.
- `requirements.txt` — Python dependencies.
- `tasks.db` — SQLite database (created at first run).

## Features

- Add tasks with deadline and notify time (date + time pickers).
- Assign tasks to a person and choose priority (High / Medium / Low).
- Filter views: All tasks, completed tasks, nearest deadlines (within 1 day).
- Desktop notifications (via `plyer`) and in-app Streamlit alerts.
- Background check every minute using `APScheduler` (scheduler is started once per Streamlit session).

## Prerequisites

- Python 3.10+ recommended (works on 3.8+).
- Windows, macOS or Linux. Desktop notification behavior depends on OS capabilities and may need enabling in system settings.
- Streamlit 1.39+ recommended.

## Quick start (PowerShell on Windows)

Open PowerShell in the project folder (`A:\coding\Python-Projects`) and run:

```powershell
# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the Streamlit app
streamlit run todolist_streamlit.py
```

If PowerShell execution policies prevent activation, run PowerShell as Administrator or temporarily allow script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## How it works

- The app stores tasks in a local `tasks.db` SQLite file in the same directory.
- The `notify_time` field determines when a desktop notification should be sent prior to the deadline.
- APScheduler runs a background job every minute to check deadlines and notify times; the scheduler is initialized one time per Streamlit session.

## Notes and troubleshooting

- Desktop notifications: Depending on OS and desktop environment, you may need to allow notifications for Python or the terminal. On Windows, notifications should appear in the Action Center. On some Linux desktops you might need `libnotify`/`notify-send` available.
- If notifications don't appear, try running the script directly (outside of Streamlit) to verify `plyer` notifications, or check the console for errors.
- The app will refuse to add tasks if the selected deadline or notify time is in the past.

## Development

- To run a local development server, use the `streamlit run` command shown above.
- To reset the database, remove `tasks.db` (or use your own backup method).

## License

This project is provided as-is for learning and small personal use.
