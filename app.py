import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
import gspread
import base64
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import json

# --- Helper Functions ---

def play_sound(sound_type="Ding"):
    try:
        # Determine which file to play
        if sound_type == "Chime":
            file_name = "chime.wav"
            icon = "🎵"
        else:
            file_name = "ding.wav"
            icon = "🔔"
        
        # Read the file as bytes (Wait ensures file is fully read)
        with open(file_name, "rb") as f:
            audio_bytes = f.read()
            
        # Play using st.audio with local bytes
        st.audio(audio_bytes, format="audio/wav", autoplay=True)
        st.toast(f"Playing {sound_type}! {icon}", icon="🔊")
        
    except FileNotFoundError:
        st.error(f"Sound file '{file_name}' not found. Please run create_sounds.py locally and push to git.")
    except Exception as e:
        st.error(f"Audio Error: {e}")

# --- Configuration ---
GOOGLE_SHEET_NAME = "pomodoro_db"
# Scope for Google Sheets and Drive API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- Helper Functions ---

def get_gspread_client():
    """Authenticates and returns the authorized client."""
    try:
        encoded_key = st.secrets["GCP_JSON_BASE64"]
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")
        creds_info = json.loads(decoded_key)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Auth Error: {str(e)}")
        return None

def init_google_sheet():
    """Returns the main worksheet (legacy helper)."""
    client = get_gspread_client()
    if client:
        return client.open(GOOGLE_SHEET_NAME).sheet1
    return None

def get_tasks_from_sheet(client):
    try:
        sheet = client.open(GOOGLE_SHEET_NAME).worksheet("Tasks")
        tasks = sheet.col_values(1)[1:] # Skip header
        return tasks
    except Exception:
        return []

def add_task_to_sheet(client, task_name):
    try:
        sheet = client.open(GOOGLE_SHEET_NAME).worksheet("Tasks")
        sheet.append_row([task_name])
    except Exception as e:
        st.error(f"Error saving task: {e}")

def delete_task_from_sheet(client, task_name):
    try:
        sheet = client.open(GOOGLE_SHEET_NAME).worksheet("Tasks")
        cell = sheet.find(task_name)
        sheet.delete_rows(cell.row)
    except Exception:
         st.warning("Could not delete task.")

def save_to_google_sheet(task_name, duration, session_type):
    """Logs a completed session to the Google Sheet."""
    sheet = init_google_sheet()
    if sheet:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        # Row to append
        row = [date_str, time_str, task_name, duration, session_type]
        
        try:
            sheet.append_row(row)
            print(">>> SUCCESS! Data saved.")
        except Exception as e:
            print(f">>> ERROR: {e}")
            st.error(f"Error saving to Google Sheet: {e}")

def get_history_from_sheet():
    """Returns the last 5 sessions from the Google Sheet."""
    sheet = init_google_sheet()
    if sheet:
        try:
            # Get all values
            data = sheet.get_all_values()
            
            # Check if there is data (assuming first row is header)
            if len(data) > 1:
                # Convert to DataFrame
                headers = data[0]
                rows = data[1:]
                df = pd.DataFrame(rows, columns=headers)
                return df.tail(5)[::-1] # Last 5, reversed order
            else:
                 return pd.DataFrame()
        except Exception as e:
            st.error(f"Error reading from Google Sheet: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def format_time(seconds):
    """Formats seconds into MM:SS string."""
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"

def show_analytics():
    st.markdown("---")
    st.header("📊 Dashboard")
    
    try:
        sheet = init_google_sheet()
        if not sheet:
            st.warning("Could not connect to database for analytics.")
            return

        # Now this works perfectly because headers exist!
        data = sheet.get_all_records()
        
        if not data:
            st.info("No data available yet.")
            return

        df = pd.DataFrame(data)
        
        # Ensure Duration is treated as a number
        if 'Duration' in df.columns:
            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce').fillna(0)
        else:
            st.error("Error: 'Duration' column missing in Google Sheet. Please add headers.")
            return

        # --- Metrics ---
        total_minutes = df['Duration'].sum()
        total_sessions = len(df)
        avg_session = df['Duration'].mean() if total_sessions > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Focus", f"{int(total_minutes)} min")
        col2.metric("Sessions", f"{total_sessions}")
        col3.metric("Avg Session", f"{int(avg_session)} min")
        
        # --- Chart 1: Daily Activity ---
        st.subheader("Daily Focus")
        if 'Date' in df.columns:
            # Group by Date and sum Duration
            daily_data = df.groupby('Date')['Duration'].sum()
            st.bar_chart(daily_data)
        
        # --- Chart 2: Task Distribution ---
        st.subheader("Top Tasks")
        if 'Task' in df.columns:
            task_data = df.groupby('Task')['Duration'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(task_data)

    except Exception as e:
        st.error(f"Analytics Error: {str(e)}")

# --- Session State Initialization ---
if 'time_left' not in st.session_state:
    st.session_state.time_left = 25 * 60 # Default to 25 mins
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_mode' not in st.session_state:
    st.session_state.timer_mode = "Work" # Work or Break
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = []

# --- UI Layout ---
st.set_page_config(page_title="Pomodoro Timer", page_icon="🍅")

# --- Helper: Print Secrets for Cloud Deployment ---
if os.path.exists("service_account.json"):
    # Only print if we are likely local (secrets might complicate this check, but file existence is good indicator)
    try:
        with open("service_account.json", "r") as f:
            data = json.load(f)
        
        print("\n\n--- [ARCHITECT] TOML for Streamlit Cloud Secrets ---\n")
        print("[gcp_service_account]")
        for k, v in data.items():
            if "\n" in str(v):
                print(f'{k} = """{v}"""')
            else:
                print(f'{k} = "{v}"')
        print("\n----------------------------------------------------\n\n")
    except Exception:
        pass

# --- Sidebar: To-Do List & Settings ---
with st.sidebar:
    st.header("📝 My Tasks")
    
    # Load client for sidebar operations
    client = get_gspread_client()
    current_tasks = []
    if client:
        current_tasks = get_tasks_from_sheet(client)
    
    new_task = st.text_input("Add a new task", placeholder="Enter task name...")
    if st.button("Add Task"):
        if new_task and new_task not in current_tasks:
            if client:
                add_task_to_sheet(client, new_task)
                st.success(f"Added: {new_task}")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Your List")
    for i, task in enumerate(current_tasks):
        col_task, col_del = st.columns([0.8, 0.2])
        col_task.write(f"• {task}")
        if col_del.button("❌", key=f"del_{i}"):
            if client:
                delete_task_from_sheet(client, task)
                st.rerun()

    st.markdown("---")
    # Settings Expander - Added expanded=True
    with st.expander("⚙️ Settings", expanded=True):
        focus_minutes = st.slider("Focus Time (min)", 5, 90, 25)
        break_minutes = st.slider("Break Time (min)", 1, 30, 5)
        theme = st.selectbox("Theme", ["Tomato 🍅", "Coffee ☕", "Code 💻", "Brain 🧠"])
        sound_choice = st.radio("Sound", ["Ding", "Chime"])

# --- Main Area ---
# Parse Emoji from Theme
emoji = theme.split()[-1]
st.title(f"{emoji} Pomodoro Focus Timer")

# Input for Task Name (Dropdown + Manual)
task_options = current_tasks + ["Type manually..."]
selected_task = st.selectbox("Select Task:", task_options)

if selected_task == "Type manually...":
    task_name = st.text_input("What are you working on?", placeholder="E.g., Finish Report", key="manual_task_input")
else:
    task_name = selected_task

# Timer Display
st.markdown(
    f"""
    <div style="text-align: center; font-size: 80px; font-weight: bold; margin: 20px 0;">
        {format_time(st.session_state.time_left)}
    </div>
    """,
    unsafe_allow_html=True
)

def start_timer(minutes, mode):
    st.session_state.timer_mode = mode
    st.session_state.time_left = minutes * 60
    st.session_state.timer_running = True
    st.rerun()

# Columns for controls
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(f"Start Focus ({focus_minutes} min)", use_container_width=True):
        start_timer(focus_minutes, "Work")

with col2:
    if st.button(f"Start Break ({break_minutes} min)", use_container_width=True):
        start_timer(break_minutes, "Break")

with col3:
    if st.button("🛠️ Test (5s)", use_container_width=True):
        # Test mode uses 5 seconds
        st.session_state.timer_mode = "Test Run"
        st.session_state.time_left = 5
        st.session_state.timer_running = True
        st.rerun()

with col4:
    if st.button("Reset", use_container_width=True):
        st.session_state.timer_running = False
        # Reset time based on current settings and mode
        if st.session_state.timer_mode == "Work":
            st.session_state.time_left = focus_minutes * 60
        elif st.session_state.timer_mode == "Break":
            st.session_state.time_left = break_minutes * 60
        else:
            st.session_state.time_left = 25 * 60
        st.rerun()

# --- Timer Logic ---
if st.session_state.timer_running:
    if st.session_state.time_left > 0:
        time.sleep(1)
        st.session_state.time_left -= 1
        st.rerun()
    else:
        # Timer finished!
        st.session_state.timer_running = False
        
        # Visual and Sound Feedback
        play_sound(sound_choice)
        st.balloons()
        st.toast("Time is up!", icon="🎉")
        
        # Log if it was work or test
        if st.session_state.timer_mode in ["Work", "Test Run"]:
            duration = focus_minutes if st.session_state.timer_mode == "Work" else 0.08 # Approx 5s
            t_name = task_name if task_name else "Untitled Task"
            
            # Save to Google Sheets
            save_to_google_sheet(t_name, duration, st.session_state.timer_mode)
            
            st.toast("Great job! Session logged.")
        elif st.session_state.timer_mode == "Break":
             st.toast("Break over! Time to focus.")

# --- History View ---
st.markdown("---")
st.subheader("Recent Sessions")

# Get history from Google Sheets
history_df = get_history_from_sheet()

if not history_df.empty:
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("No sessions logged yet.")

# --- Analytics Dashboard ---
show_analytics()
