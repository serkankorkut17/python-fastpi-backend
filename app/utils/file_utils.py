# compression examples for other file types
import gzip
import shutil


def compress_text_file(input_file_path, output_file_path):
    with open(input_file_path, "rb") as input_file:
        with gzip.open(output_file_path, "wb") as output_file:
            shutil.copyfileobj(input_file, output_file)


# compress_text_file('example.txt', 'example.txt.gz')

import zipfile


def compress_json_file(input_file_path, output_file_path):
    with zipfile.ZipFile(output_file_path, "w") as zipf:
        zipf.write(input_file_path)


# compress_json_file('data.json', 'data.zip')


import tarfile


def compress_csv_file(input_file_path, output_file_path):
    with tarfile.open(output_file_path, "w:gz") as tar:
        tar.add(input_file_path, arcname=input_file_path.split("/")[-1])


# compress_csv_file('data.csv', 'data.tar.gz')


import zipfile


def compress_pdf_file(input_file_path, output_file_path):
    with zipfile.ZipFile(output_file_path, "w") as zipf:
        zipf.write(input_file_path)


# compress_pdf_file("document.pdf", "document.zip")


import zipfile
import os


def compress_directory(input_directory, output_zip):
    with zipfile.ZipFile(output_zip, "w") as zipf:
        for root, _, files in os.walk(input_directory):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)


# compress_directory('my_folder', 'my_folder.zip')
