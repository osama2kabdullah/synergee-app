from app import create_app
from app.routes.api import loop_over_all_stores
import datetime
import os

app = create_app()

LOG_FILE = "task.log"

def log(message):
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(hours=24)
    lines_to_keep = []

    # Read and filter existing log lines
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    # Extract timestamp: [YYYY-MM-DD HH:MM:SS]
                    timestamp_str = line.split("]")[0].strip("[")
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    
                    # Keep only last 24 hours
                    if timestamp >= cutoff:
                        lines_to_keep.append(line)
                except:
                    # If parsing fails, drop the line (or keep it if you want)
                    pass

    # Add the new log line
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    new_line = f"[{timestamp_str}] {message}\n"
    lines_to_keep.append(new_line)

    # Write back only kept lines
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines_to_keep)


if __name__ == "__main__":
    with app.app_context():
        loop_over_all_stores()
        log("Completed looping over all stores")
