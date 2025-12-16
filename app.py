import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
import json

# --- Configuration ---
# LOG_FILE = "pomodoro_log.xlsx" # Commented out for Google Sheets
GOOGLE_SHEET_NAME = "pomodoro_db"
# Scope for Google Sheets and Drive API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- Helper Functions ---

def init_google_sheet():
    """Authenticates, returns sheet, and ensures headers exist."""
    try:
        # Hybrid Authentication: Secrets (Cloud) vs Local File (Dev)
        if "gcp_service_account" in st.secrets:
            # Cloud: Load from secrets
            creds_dict = dict(st.secrets["gcp_service_account"]) # Create a copy
            
            # Fix for literal \n in private_key (common Streamlit Cloud issue)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        else:
            # Local: Load from file (Fallback)
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPE)
            
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1 # Assumes data is in the first sheet

        # Ensure headers exist if empty
        if not sheet.get_all_values():
            headers = ["Date", "Time", "Task Name", "Duration (mins)", "Type"]
            sheet.append_row(headers)

        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
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
col1, col2, col3 = st.columns(3)

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
    if st.button("Reset", use_container_width=True):
        st.session_state.timer_running = False
        # Reset time based on current mode
        if st.session_state.timer_mode == "Work":
            st.session_state.time_left = 25 * 60
        else:
            st.session_state.time_left = 5 * 60
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
        
        # Play a sound (optional, mostly visual here)
        st.success("Timer Finished!")
        
        # Log if it was work
        if st.session_state.timer_mode == "Work":
            duration = 25
            t_name = task_name if task_name else "Untitled Task"
            
            # Save to Google Sheets instead of Excel
            print(">>> STARTING SAVE TO GOOGLE SHEETS...")
            save_to_google_sheet(t_name, duration, "Work")
            # save_to_excel(t_name, duration, "Work")
            
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

# --- Debug: Cloud Connection Test ---
st.sidebar.header("Debug Tools")
if st.sidebar.button("Test Google Connection"):
    try:
        # Use existing logic to get sheet
        sheet = init_google_sheet() 
        if sheet:
            # Try appending dummy row
            row = ["TEST", "DEBUG", "Connection Test", "0", "Debug"]
            sheet.append_row(row)
            st.sidebar.success("Connection Verified! Row added.")
        else:
            st.sidebar.error("Failed to initialize sheet (returned None).")
    except Exception as e:
        st.sidebar.error(f"Connection Failed: {e}")
