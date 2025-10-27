import streamlit as st
from plyer import notification
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Constants
DB_NAME = 'tasks.db'
DATETIME_FORMAT = '%Y-%m-%d %H:%M'

# ============================================================================
# Database Functions
# ============================================================================

def init_db():
    """Initialize the database and create tasks table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create table with all columns
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        deadline TEXT NOT NULL,
        notify_time TEXT NOT NULL,
        assigned_by TEXT NOT NULL DEFAULT '',
        designation TEXT NOT NULL DEFAULT '',
        priority TEXT NOT NULL DEFAULT 'Medium',
        completed INTEGER NOT NULL DEFAULT 0
    )''')
    # Migrate old table if columns don't exist
    c.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in c.fetchall()]
    if 'notify_time' not in columns:
        c.execute('ALTER TABLE tasks ADD COLUMN notify_time TEXT NOT NULL DEFAULT "1970-01-01 00:00"')
    if 'assigned_by' not in columns:
        c.execute('ALTER TABLE tasks ADD COLUMN assigned_by TEXT NOT NULL DEFAULT ""')
    if 'designation' not in columns:
        c.execute('ALTER TABLE tasks ADD COLUMN designation TEXT NOT NULL DEFAULT ""')
    if 'priority' not in columns:
        c.execute('ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT "Medium"')
    
    conn.commit()
    conn.close()


def add_task(name, deadline, notify_time, assigned_by, designation, priority):
    """Add a new task to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'INSERT INTO tasks (name, deadline, notify_time, assigned_by, designation, priority, completed) VALUES (?, ?, ?, ?, ?, ?, 0)',
        (name, deadline, notify_time, assigned_by, designation, priority)
    )
    conn.commit()
    conn.close()


def get_tasks():
    """Retrieve all tasks from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, deadline, notify_time, assigned_by, designation, priority, completed FROM tasks')
    tasks = c.fetchall()
    conn.close()
    return tasks


def update_task(task_id, name, deadline, notify_time, assigned_by, designation, priority, completed):
    """Update an existing task in the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'UPDATE tasks SET name=?, deadline=?, notify_time=?, assigned_by=?, designation=?, priority=?, completed=? WHERE id=?',
        (name, deadline, notify_time, assigned_by, designation, priority, completed, task_id)
    )
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Delete a task from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()


# ============================================================================
# Notification Functions
# ============================================================================

def check_deadlines():
    """Check all tasks and send notifications for approaching or overdue deadlines."""
    tasks = get_tasks()
    now = datetime.now()
    
    for task in tasks:
        task_id, name, deadline, notify_time, assigned_by, designation, priority, completed = task
        
        # Skip completed tasks
        if completed:
            continue
        
        deadline_dt = datetime.strptime(deadline, DATETIME_FORMAT)
        notify_dt = datetime.strptime(notify_time, DATETIME_FORMAT)
        
        # Check if it's time to send notification
        if now >= notify_dt and notify_dt > datetime(1970, 1, 1):
            notification.notify(
                title="Task Notification",
                message=f"Task '{name}' notification time reached!",
                timeout=10
            )
            st.info(f"Task '{name}' notification time reached!")
        
        # Check for overdue tasks
        if deadline_dt < now:
            notification.notify(
                title="Task Overdue!",
                message=f"Task '{name}' is overdue!",
                timeout=10
            )
            st.warning(f"Task '{name}' is overdue!")
        
        # Check for approaching deadlines (within 30 minutes)
        elif deadline_dt - now < timedelta(minutes=30):
            notification.notify(
                title="Task Deadline Approaching",
                message=f"Task '{name}' deadline is approaching!",
                timeout=10
            )
            st.info(f"Task '{name}' deadline is approaching!")


# ============================================================================
# Task Filtering Functions
# ============================================================================

def filter_tasks(tasks, filter_option):
    """Filter tasks based on the selected option."""
    now = datetime.now()
    
    if filter_option == 'View Completed Tasks':
        # Return all completed tasks (both past and present)
        return [task for task in tasks if task[7] == 1]
    
    elif filter_option == 'View Nearest Deadline Tasks (within 1 day)':
        filtered = []
        for task in tasks:
            if not task[7]:  # Not completed
                deadline_dt = datetime.strptime(task[2], DATETIME_FORMAT)
                if deadline_dt - now < timedelta(days=1):
                    filtered.append(task)
        return filtered
    
    return tasks  # All tasks


# ============================================================================
# Scheduler Setup
# ============================================================================

def init_scheduler():
    """Initialize the background scheduler for checking deadlines."""
    if 'scheduler_started' not in st.session_state:
        scheduler = BackgroundScheduler()
        scheduler.add_job(check_deadlines, 'interval', minutes=1)
        scheduler.start()
        st.session_state['scheduler_started'] = True


# ============================================================================
# Main Application
# ============================================================================

def main():
    st.title('📝 To-Do List App')
    
    # Initialize database and scheduler
    init_db()
    init_scheduler()
    
    # Task filter - using radio buttons to prevent editing
    st.subheader('Filter Tasks')
    filter_option = st.radio(
        'Select view:',
        options=[
            'All Tasks',
            'View Completed Tasks',
            'View Nearest Deadline Tasks (within 1 day)'
        ],
        index=0,
        horizontal=False
    )
    
    # Add new task section
    st.header('Add New Task')
    with st.form('add_task_form', clear_on_submit=True):
        name = st.text_input('Task Name')
        col_assign1, col_assign2 = st.columns(2)
        with col_assign1:
            assigned_by = st.text_input('Assigned By (Person Name)', help='Enter the name of the person who assigned this task')
        with col_assign2:
            designation = st.text_input('Designation', help='Enter the designation/position of the person')
        priority = st.selectbox('Priority', ['High', 'Medium', 'Low'], index=1)
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input('Deadline Date')
            deadline_time = st.time_input('Deadline Time', step=300)
        with col2:
            notify_date = st.date_input('Notify Date')
            notify_time_val = st.time_input('Notify Time', step=300)
        submitted = st.form_submit_button('Add Task', use_container_width=True)
        if submitted:
            now = datetime.now()
            if not name:
                st.error('Please enter a task name!')
            elif not assigned_by:
                st.error('Please enter the name of the person who assigned the task!')
            elif not designation:
                st.error('Please enter the designation of the person!')
            else:
                try:
                    deadline_dt = datetime.combine(deadline_date, deadline_time)
                    notify_dt = datetime.combine(notify_date, notify_time_val)
                    if deadline_dt < now or notify_dt < now:
                        st.error('Date is invalid. You cannot select past dates for deadline or notify time.')
                    else:
                        deadline_str = deadline_dt.strftime(DATETIME_FORMAT)
                        notify_str = notify_dt.strftime(DATETIME_FORMAT)
                        add_task(name, deadline_str, notify_str, assigned_by, designation, priority)
                        st.success('Task added successfully!')
                        st.rerun()
                except Exception as e:
                    st.error(f'Error adding task: {e}')
    
    # Display tasks section
    st.header('Tasks')
    tasks = get_tasks()
    
    if not tasks:
        st.info('No tasks found. Add a new task to get started!')
    else:
        # Filter tasks based on selection
        filtered_tasks = filter_tasks(tasks, filter_option)
        
        if not filtered_tasks:
            st.info(f'No tasks found for the selected filter.')
        else:
            # Display tasks in a table-like format
            for task in filtered_tasks:
                task_id, name, deadline, notify_time, assigned_by, designation, priority, completed = task
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2, 1.5, 1])
                    with col1:
                        st.write(f"**{name}**")
                    with col2:
                        st.write(f"🗓️ {deadline}")
                    with col3:
                        st.write(f"🔔 {notify_time}")
                    with col4:
                        st.write(f"👤 {assigned_by}")
                        st.caption(f"📋 {designation}")
                    with col5:
                        st.write(f"🏷️ {priority}")
                    with col6:
                        # Toggle completion status
                        if st.checkbox(
                            'Complete',
                            value=bool(completed),
                            key=f'complete_{task_id}'
                        ):
                            if not completed:
                                update_task(task_id, name, deadline, notify_time, assigned_by, designation, priority, 1)
                                st.rerun()
                        else:
                            if completed:
                                update_task(task_id, name, deadline, notify_time, assigned_by, designation, priority, 0)
                                st.rerun()
                    with col7:
                        if st.button('🗑️', key=f'delete_{task_id}', help='Delete task'):
                            delete_task(task_id)
                            st.rerun()
                    st.divider()
    
    # Check deadlines
    check_deadlines()


if __name__ == '__main__':
    main()