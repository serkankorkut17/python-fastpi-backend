import os
from celery import Celery
from dotenv import load_dotenv
import time

# Load environment variables from the .env file
load_dotenv(".env")

# Create a new Celery instance
celery = Celery(__name__)

# Configure Celery with broker URL and result backend from environment variables
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

# import app.tasks.task_example
@celery.task(name="task_example")
def task_example(a: int, b: int):
    time.sleep(a + b)
    return "Task completed successfully"
