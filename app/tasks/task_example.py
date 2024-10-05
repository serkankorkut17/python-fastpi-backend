from celery import shared_task

import time

@shared_task
def task_example(a: int, b: int):
    time.sleep(a + b)
    return "Task completed successfully"