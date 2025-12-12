import subprocess
import schedule
import sys
from time import sleep
from datetime import datetime,date

SCHEDULED_TIME = "15:30"
EVERY_SECOND = ":40"
EVERY_MINUTE = 1

def task():
    print("Run operation test")
    subprocess.run([sys.executable, "py/operational_test.py", "--yaml-file", "py/operation/normal.yaml"])


if __name__ == "__main__":
    # Run the task function every day at SCHEDULED_TIME
    schedule.every().days.at(SCHEDULED_TIME).do(task)
    print(f"Scheduled to run at {SCHEDULED_TIME}")

    # Execute task function every minute at EVERY_SECOND seconds
    # schedule.every().minute.at(EVERY_SECOND).do(task)
    # print(f"Scheduled to run every minute at {SCHEDULED_TIME} seconds.")

    # Run the task function every EVERY_MINUTE minutes
    # schedule.every(EVERY_MINUTE).minutes.do(task)
    # print(f"Scheduled to run at {EVERY_MINUTE} minutes.")

    # Event execution
    while True:
        schedule.run_pending()
        sleep(1)
