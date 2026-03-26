import datetime
import os

def log(file, message):
    """Log message to file with timestamp"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "a") as f:
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except Exception as e:
        print(f"Error writing to log file {file}: {e}")