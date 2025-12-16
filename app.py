import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime

# --- Configuration ---
LOG_FILE = "pomodoro_log.xlsx"

# --- Helper Functions ---
def save_to_excel(task_name, duration, session_type):
    """Logs a completed session to the Excel file."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    new_data = {
        "Date": [date_str],
        "Time": [time_str],
        "Task Name": [task_name],
        "Duration (mins)": [duration],
        "Type": [session_type]
    }
    df_new = pd.DataFrame(new_data)
    
    if os.path.exists(LOG_FILE):
        try:
            # Append to existing file
            with pd.ExcelWriter(LOG_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Load existing to find the last row, or just append simply
                # Easier way with pandas: Load, concat, save back.
                # For simplicity and robustness against empty files:
                df_existing = pd.read_excel(LOG_FILE)
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
                df_final.to_excel(LOG_FILE, index=False)
        except Exception as e:
            st.error(f"Error saving to Excel: {e}")
    else:
        # Create new file
        df_new.to_excel(LOG_FILE, index=False)

def get_history():
    """Returns the last 5 sessions from the Excel file."""
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_excel(LOG_FILE)
            return df.tail(5)[::-1] # Last 5, reversed order
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

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
            save_to_excel(t_name, duration, "Work")
            st.toast("Great job! Session logged.")
        elif st.session_state.timer_mode == "Break":
             st.toast("Break over! Time to focus.")

# --- History View ---
st.markdown("---")
st.subheader("Recent Sessions")
history_df = get_history()

if not history_df.empty:
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("No sessions logged yet.")
