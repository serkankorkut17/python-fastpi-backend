import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv(".env")

# Create a new Celery instance
celery = Celery(__name__)

# Configure Celery with broker URL and result backend from environment variables
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

# Import tasks so that they are registered with the Celery app
import app.tasks.task_example
