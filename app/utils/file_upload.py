import os
import shutil
from fastapi import HTTPException
from datetime import datetime

from app.utils.video_utils import compress_video, is_ffmpeg_installed
from app.utils.image_utils import compress_image


# Define a function to handle file uploads
def handle_file_upload(uploaded_file, upload_folder):
    # Check if the file was uploaded
    if uploaded_file is None:
        return None

    # Create an uploads directory if it doesn't exist
    upload_directory = os.path.join("./uploads", upload_folder)
    os.makedirs(
        upload_directory, exist_ok=True
    )  # Create the directory if it doesn't exist
    # Create a temp directory to store the uploaded file
    os.makedirs(os.path.join(upload_directory, "temp"), exist_ok=True)
    # Create a unique filename using the current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    original_filename = uploaded_file.filename

    # Extract the base filename and extension
    base_filename, extension = os.path.splitext(original_filename)
    base_filename = base_filename.split("/")[-1]

    # Define a temporary file path
    temp_file_path = os.path.join(
        upload_directory, "temp", f"{timestamp}_{base_filename}"
    )

    # Save the uploaded file to the temp directory
    with open(temp_file_path, "wb") as destination:
        shutil.copyfileobj(uploaded_file.file, destination)

    # Define the output file path based on file type
    output_file_path = None

    try:
        # Check file type to determine processing
        if uploaded_file.content_type.startswith("image/"):
            # Define the output file path with the WebP extension
            output_file_path = os.path.join(
                upload_directory, f"{timestamp}_{base_filename}.webp"
            )
            compress_image(temp_file_path, output_file_path)  # Convert to WebP
        elif is_ffmpeg_installed() and uploaded_file.content_type.startswith("video/"):
            output_file_path = os.path.join(
                upload_directory, f"{timestamp}_{base_filename}.webm"
            )
            compress_video(
                temp_file_path,
                output_file_path,
                quality=35,
                speed=8,
                max_width=1920,
                max_height=1080,
            )  # Compress video
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload an image or video.",
            )
    except Exception as e:
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="File processing failed.")

    # Remove the temporary file after processing
    os.remove(temp_file_path)
    # return output file path and media type
    return output_file_path, uploaded_file.content_type
