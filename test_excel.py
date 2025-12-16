import pandas as pd
import os
from datetime import datetime

LOG_FILE = "pomodoro_log.xlsx"

def save_to_excel(task_name, duration, session_type):
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
            with pd.ExcelWriter(LOG_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Naive append for test
                df_existing = pd.read_excel(LOG_FILE)
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
                df_final.to_excel(LOG_FILE, index=False)
            print("Appended to existing file.")
        except Exception as e:
            print(f"Error saving to Excel: {e}")
    else:
        df_new.to_excel(LOG_FILE, index=False)
        print("Created new file.")

def test():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        print("Removed old log file.")

    print("Testing create new file...")
    save_to_excel("Test Task 1", 25, "Work")
    
    assert os.path.exists(LOG_FILE)
    df = pd.read_excel(LOG_FILE)
    assert len(df) == 1
    assert df.iloc[0]["Task Name"] == "Test Task 1"
    
    print("Testing append...")
    save_to_excel("Test Task 2", 25, "Work")
    df = pd.read_excel(LOG_FILE)
    assert len(df) == 2
    assert df.iloc[1]["Task Name"] == "Test Task 2"
    
    print("SUCCESS: Excel logging logic verified.")

if __name__ == "__main__":
    test()
