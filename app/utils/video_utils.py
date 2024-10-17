# import ffmpeg
# import os

# def compress_video(input_video_path, output_video_path, quality=23, preset='medium'):
#     """
#     Compresses a video using ffmpeg with the specified quality and preset.
#     - input_video_path: The input video file path.
#     - output_video_path: The output compressed video file path.
#     - quality: A value from 0 (best quality, larger size) to 51 (worst quality, smaller size). Default is 23.
#     - preset: A value from 'ultrafast' (less compression, bigger file) to 'slower' (better compression, smaller file). Default is 'medium'.
#     """
#     ffmpeg.input(input_video_path).output(output_video_path, 
#                                           vcodec='libvpx-vp9', 
#                                           crf=quality, 
#                                           preset=preset).run()
    
#     print(f"Successfully compressed {input_video_path} to {output_video_path} with quality={quality} and preset={preset}")

# def convert_to_webm(input_video_path, output_video_path):
#     """
#     Converts a video to the WebM format using ffmpeg.
#     - input_video_path: The input video file path.
#     - output_video_path: The output WebM video file path.
#     """
#     ffmpeg.input(input_video_path).output(output_video_path, vcodec='libvpx-vp9').run()
    
#     print(f"Successfully converted {input_video_path} to {output_video_path}")

# # quality (crf): Controls the quality of the video (lower values result in higher quality but larger files). For libvpx-vp9, the recommended range is 15-35, with 23 as a default.
# # preset: Controls the speed vs compression efficiency. Options include ultrafast, fast, medium, slow, and slower. Faster presets result in larger file sizes but quicker compression, while slower presets yield smaller file sizes at the cost of time.

# # Example usage
# input_video = 'input_video.mp4'
# output_video = 'output_video.webm'
# compress_video(input_video, output_video)
