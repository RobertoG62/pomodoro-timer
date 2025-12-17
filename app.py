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
    # Reliable source: Glass Ping from Wikimedia
    sound_url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Glass_ping.wav"
    
    # HTML5 Audio with autoplay
    st.markdown(f"""
        <audio autoplay="true">
        <source src="{sound_url}" type="audio/wav">
        </audio>
        """, unsafe_allow_html=True)
        
    # Optional: Add a small text indicator just to be sure function ran
    st.caption("🔔 Sound playing...")

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

# --- Session State Initialization ---
if 'time_left' not in st.session_state:
    st.session_state.time_left = 25 * 60 # Default to 25 mins
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_mode' not in st.session_state:
    st.session_state.timer_mode = "Work" # Work or Break

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

# Input for Task Name
task_name = st.text_input("Task Name", placeholder="What are you working on?", key="task_input")

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


