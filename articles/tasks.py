# app/tasks.py
from celery import shared_task
import time

@shared_task
def add(x, y):
    for i in range(5):
        print("Processing...")
        time.sleep(1)  # Sleep for 1 second in each iteration
    print(f"Adding {x} and {y}")
    return x + y