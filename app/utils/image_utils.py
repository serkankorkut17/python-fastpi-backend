from PIL import Image
import shutil
import os

def compress_image(input_image_path, output_image_path, quality=75, lossless=False, effort=4):
    with Image.open(input_image_path) as img:
        img.save(output_image_path, 'webp', quality=quality, lossless=lossless, method=effort)
    print(f"Successfully converted {input_image_path} to {output_image_path} with quality={quality}, lossless={lossless}, effort={effort}")
    
def convert_to_webp(input_path, output_path):
    # Open an image file
    with Image.open(input_path) as img:
        # Convert to WebP format
        img.save(output_path, 'webp')
