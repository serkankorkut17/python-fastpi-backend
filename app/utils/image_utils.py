from PIL import Image


# Function to compress an image using the WebP format
def compress_image(
    input_image_path, output_image_path, quality=75, lossless=False, effort=4
):
    with Image.open(input_image_path) as img:
        img.save(
            output_image_path, "webp", quality=quality, lossless=lossless, method=effort
        )
    # print(f"Successfully converted {input_image_path} to {output_image_path} with quality={quality}, lossless={lossless}, effort={effort}")


# Function to convert an image to WebP format
def convert_to_webp(input_path, output_path):
    # Open an image file
    with Image.open(input_path) as img:
        # Convert to WebP format
        img.save(output_path, "webp")
