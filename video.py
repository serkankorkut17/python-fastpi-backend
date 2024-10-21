import ffmpeg
import os
import subprocess
import sys


def is_ffmpeg_installed():
    """Check if FFmpeg is installed on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def compress_video(
    input_video_path,
    output_video_path,
    quality=23,
    preset="medium",
    speed=5,
    max_width=1920,
    max_height=1080,
):
    """
    Compresses a video using ffmpeg with the specified quality and preset.
    If the resolution is too high, it downgrades the resolution.
    - input_video_path: The input video file path.
    - output_video_path: The output compressed video file path.
    - quality: A value from 0 (best quality, larger size) to 51 (worst quality, smaller size). Default is 23.
    - preset: A value from 'ultrafast' (less compression, bigger file) to 'slower' (better compression, smaller file). Default is 'medium'. (!!! not working for this codec)
    -The speed option takes values from 0 (slowest, best quality) to 8 (fastest, lower quality). A value of 2 to 5 is often a good balance.
    - max_width: The maximum width for the output video.
    - max_height: The maximum height for the output video.
    """
    probe = ffmpeg.probe(input_video_path)
    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )

    if video_stream:
        width = int(video_stream["width"])
        height = int(video_stream["height"])
        print(f"Original Resolution: {width}x{height}")

        # Check if the resolution exceeds the max width or height
        if width > max_width or height > max_height:
            # Calculate new resolution while maintaining aspect ratio
            aspect_ratio = width / height
            if width > height:
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            print(f"Downgrading resolution to: {new_width}x{new_height}")
        else:
            new_width = width
            new_height = height
    else:
        print("No video stream found.")
        return

    ffmpeg.input(input_video_path).output(
        output_video_path,
        vcodec="libvpx-vp9",
        crf=quality,
        # preset=preset,
        speed=speed,
        s=f"{new_width}x{new_height}",  # Set the output resolution
    ).run()

    print(
        f"Successfully compressed {input_video_path} to {output_video_path} with quality={quality} and preset={preset}"
    )


def convert_to_webm(input_video_path, output_video_path):
    """
    Converts a video to the WebM format using ffmpeg.
    - input_video_path: The input video file path.
    - output_video_path: The output WebM video file path.
    """
    ffmpeg.input(input_video_path).output(output_video_path, vcodec="libvpx-vp9").run()

    print(f"Successfully converted {input_video_path} to {output_video_path}")


# quality (crf): Controls the quality of the video (lower values result in higher quality but larger files). For libvpx-vp9, the recommended range is 15-35, with 23 as a default.
# preset: Controls the speed vs compression efficiency. Options include ultrafast, fast, medium, slow, and slower. Faster presets result in larger file sizes but quicker compression, while slower presets yield smaller file sizes at the cost of time.

# Example usage
# Check if
if not is_ffmpeg_installed():
    print("FFmpeg is not installed. Please install FFmpeg to use this script.")
    sys.exit(1)
else:
    print("FFmpeg is installed.")
input_video = "uploads/uhd_3840_2160_25fps.mp4"
compressed_video = "uploads/compressed_video.webm"
compress_video(
    input_video,
    compressed_video,
    quality=35,
    speed=8,
    max_width=1920,
    max_height=1080,
)
