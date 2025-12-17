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

def play_sound():
    # Embedded Base64 audio (0.5s 880Hz Sine Wave Beep)
    audio_base64 = "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"

    audio_bytes = base64.b64decode(audio_base64)
    st.audio(audio_bytes, format='audio/wav', autoplay=True)
    
    st.toast("Ring Ring! 🔔", icon="🔊")

# --- Configuration ---
# LOG_FILE = "pomodoro_log.xlsx" # Commented out for Google Sheets
GOOGLE_SHEET_NAME = "pomodoro_db"
# Scope for Google Sheets and Drive API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- Helper Functions ---

def init_google_sheet():
    """Authenticates using Base64 encoded secrets (Final Solution)."""
    try:
        # Decode the Base64 string from secrets
        encoded_key = st.secrets["GCP_JSON_BASE64"]
        decoded_key = base64.b64decode(encoded_key).decode("utf-8")
        creds_info = json.loads(decoded_key)
        
        # Create credentials
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        return sheet
        
    except Exception as e:
        st.error(f"Auth Error: {str(e)}")
        return None

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

# Original Excel Logic (Commented Out)
# def save_to_excel(task_name, duration, session_type):
#     """Logs a completed session to the Excel file."""
#     now = datetime.now()
#     date_str = now.strftime("%Y-%m-%d")
#     time_str = now.strftime("%H:%M:%S")
#     
#     new_data = {
#         "Date": [date_str],
#         "Time": [time_str],
#         "Task Name": [task_name],
#         "Duration (mins)": [duration],
#         "Type": [session_type]
#     }
#     df_new = pd.DataFrame(new_data)
#     
#     if os.path.exists(LOG_FILE):
#         try:
#             # Append to existing file
#             with pd.ExcelWriter(LOG_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
#                 # Load existing to find the last row, or just append simply
#                 # Easier way with pandas: Load, concat, save back.
#                 # For simplicity and robustness against empty files:
#                 df_existing = pd.read_excel(LOG_FILE)
#                 df_final = pd.concat([df_existing, df_new], ignore_index=True)
#                 df_final.to_excel(LOG_FILE, index=False)
#         except Exception as e:
#             st.error(f"Error saving to Excel: {e}")
#     else:
#         # Create new file
#         df_new.to_excel(LOG_FILE, index=False)

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

# Start of original get_history
# def get_history():
#     """Returns the last 5 sessions from the Excel file."""
#     if os.path.exists(LOG_FILE):
#         try:
#             df = pd.read_excel(LOG_FILE)
#             return df.tail(5)[::-1] # Last 5, reversed order
#         except Exception:
#             return pd.DataFrame()
#     return pd.DataFrame()

def format_time(seconds):
    """Formats seconds into MM:SS string."""
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"

def show_analytics():
    st.markdown("---")
    st.header("📊 Dashboard")
    
    try:
        # Fetch data using existing helper
        sheet = init_google_sheet()
        if not sheet:
            st.warning("Could not connect to database for analytics.")
            return

        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            st.info("No data available for analytics yet.")
            return

        # Basic Cleanup & Conversions
        # Adapt to actual column names: "Duration (mins)" and "Task Name"
        duration_col = 'Duration (mins)' if 'Duration (mins)' in df.columns else 'Duration'
        
        if duration_col in df.columns:
            df['Duration'] = pd.to_numeric(df[duration_col], errors='coerce').fillna(0)
        else:
            st.warning("Duration column not found.")
            return
        
        # Metrics
        total_minutes = df['Duration'].sum()
        total_sessions = len(df)
        avg_session = df['Duration'].mean()
        
        # Display Metrics in Columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Focus Time", f"{int(total_minutes)} min")
        col2.metric("Total Sessions", f"{total_sessions}")
        col3.metric("Avg Session", f"{int(avg_session)} min")
        
        # Chart 1: Daily Activity (Bar Chart)
        st.subheader("Daily Focus (Minutes)")
        if 'Date' in df.columns:
            # Group by Date and sum Duration
            daily_data = df.groupby('Date')['Duration'].sum()
            st.bar_chart(daily_data)
        
        # Chart 2: Task Distribution (Bar Chart)
        st.subheader("Focus by Task")
        task_col = 'Task Name' if 'Task Name' in df.columns else 'Task'
        if task_col in df.columns:
            task_data = df.groupby(task_col)['Duration'].sum().sort_values(ascending=False).head(5) # Top 5 tasks
            st.bar_chart(task_data)
            
    except Exception as e:
        st.error(f"Could not load analytics: {str(e)}")

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

st.title("🍅 Pomodoro Focus Timer")

# --- Sidebar: To-Do List ---
with st.sidebar:
    st.header("📝 My Tasks")
    new_task = st.text_input("Add a new task", placeholder="Enter task name...")
    if st.button("Add Task"):
        if new_task and new_task not in st.session_state['tasks']:
            st.session_state['tasks'].append(new_task)
            st.success(f"Added: {new_task}")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Your List")
    for i, task in enumerate(st.session_state['tasks']):
        col_task, col_del = st.columns([0.8, 0.2])
        col_task.write(f"• {task}")
        if col_del.button("❌", key=f"del_{i}"):
            st.session_state['tasks'].pop(i)
            st.rerun()

# Input for Task Name (Dropdown + Manual)
task_options = st.session_state['tasks'] + ["Type manually..."]
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

# columns for controls
# columns for controls
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Start 25m Focus", use_container_width=True):
        st.session_state.timer_mode = "Work"
        st.session_state.time_left = 25 * 60
        st.session_state.timer_running = True
        st.rerun()

with col2:
    if st.button("Start 5m Break", use_container_width=True):
        st.session_state.timer_mode = "Break"
        st.session_state.time_left = 5 * 60
        st.session_state.timer_running = True
        st.rerun()

with col3:
    if st.button("🛠️ Test (5s)", use_container_width=True):
        st.session_state.timer_mode = "Test Run"
        st.session_state.time_left = 5
        st.session_state.timer_running = True
        st.rerun()

with col4:
    if st.button("Reset", use_container_width=True):
        st.session_state.timer_running = False
        # Reset time based on current mode
        if st.session_state.timer_mode == "Work":
            st.session_state.time_left = 25 * 60
        elif st.session_state.timer_mode == "Break":
            st.session_state.time_left = 5 * 60
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
        play_sound()
        st.balloons()
        st.toast("Time is up!", icon="🎉")
        st.success("Timer Finished!")
        
        # Log if it was work or test
        if st.session_state.timer_mode in ["Work", "Test Run"]:
            duration = 25 if st.session_state.timer_mode == "Work" else 0.08
            t_name = task_name if task_name else "Untitled Task"
            
            # Save to Google Sheets
            print(">>> STARTING SAVE TO GOOGLE SHEETS...")
            save_to_google_sheet(t_name, duration, st.session_state.timer_mode)
            
            st.toast("Great job! Session logged.")
        elif st.session_state.timer_mode == "Break":
             st.toast("Break over! Time to focus.")

# --- History View ---
st.markdown("---")
st.subheader("Recent Sessions")

# Get history from Google Sheets
history_df = get_history_from_sheet()
# history_df = get_history()

if not history_df.empty:
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("No sessions logged yet.")

# --- Analytics Dashboard ---
show_analytics()


