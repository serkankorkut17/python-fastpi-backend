import os
import shutil
from fastapi import HTTPException
from PIL import Image
from app.utils.video_utils import compress_video
from app.utils.image_utils import compress_image
from datetime import datetime

def handle_file_upload(uploaded_file, upload_folder):
    """Handles the process of saving and converting an uploaded file to the appropriate format."""
    if uploaded_file is None:
        return None

    upload_directory = os.path.join("./uploads", upload_folder)
    os.makedirs(upload_directory, exist_ok=True)  # Create the directory if it doesn't exist

    # Create a unique filename using the current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = uploaded_file.filename
    base_filename, extension = os.path.splitext(original_filename)
    
    # Define a temporary file path
    temp_file_path = os.path.join(upload_directory, f"temp_{timestamp}_{original_filename}")

    with open(temp_file_path, "wb") as destination:
        shutil.copyfileobj(uploaded_file.file, destination)

    # Define the output file path based on file type
    output_file_path = None

    try:
        # Check file type to determine processing
        if uploaded_file.content_type.startswith('image/'):
            output_file_path = os.path.join(upload_directory, f"{timestamp}_{base_filename}.webp")
            compress_image(temp_file_path, output_file_path)  # Convert to WebP
        elif uploaded_file.content_type.startswith('video/'):
            output_file_path = os.path.join(upload_directory, f"{timestamp}_{base_filename}.webm")
            compress_video(temp_file_path, output_file_path)  # Compress video
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an image or video.")
    except Exception as e:
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="File processing failed.")

    # Remove the temporary file after processing
    os.remove(temp_file_path)
    
    return output_file_path  # Return the path to the processed file