import os
import logging

# Create a logs directory if it doesn't exist
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Define the log file path
log_file = os.path.join(log_directory, "app.log")

# Delete the log file if it exists
if os.path.exists(log_file):
    os.remove(log_file)

# Configure logging to output to a file
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO or DEBUG for more detailed output
    format="%(asctime)s [%(levelname)s] %(message)s",  # Format for log messages
    handlers=[
        logging.FileHandler(log_file),  # Output logs to the specified file
        logging.StreamHandler(),  # Output logs to the console
    ],
)

# Create a logger instance
logger = logging.getLogger(__name__)
