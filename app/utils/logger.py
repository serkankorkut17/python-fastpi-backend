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


# Configure logging to output to a file and the console
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO
    format="%(asctime)s [%(levelname)s] %(message)s",  # Added function name to log format
    handlers=[
        logging.FileHandler(log_file),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)

# Create a logger instance
logger = logging.getLogger(__name__)


# logger.info(f"Request headers: {info.context['request'].headers}")
# logger.info(f"Request method: {info.context['request'].method}")

# request = info.context["request"]
# logger.info(f"Request: {dir(request)}")

# # Read and log request body as JSON
# req_body = await request.body()

# # Convert the request body to a string for printing
# body_str = req_body.decode("utf-8") if isinstance(req_body, bytes) else str(req_body)

# # Log the request body
# logger.info(f"Request body: {body_str}")
# # Log request details
# logger.info(f"Request headers: {request.headers}")
# logger.info(f"Request method: {request.method}")
# logger.info(f"Request URL: {request.url}")
# logger.info(f"Request query parameters: {request.query_params}")
# logger.info(f"Request path parameters: {request.path_params}")
# logger.info(f"Request client: {request.client}")
# logger.info(f"Request cookies: {request.cookies}")
