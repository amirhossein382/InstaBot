import mimetypes
from uuid import uuid4


def change_filename(filename: str) -> str:
    return f"{uuid4()}.{filename.split('.')[-1]}"


def is_video(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith("video")


def is_image(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith("image")
