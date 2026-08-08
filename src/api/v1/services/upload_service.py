import os
import uuid
import requests
from fastapi import UploadFile
from src.ingestion.ingestion import ingest_pdf

UPLOAD_DIR = "data/uploads"


def download_pdf_from_url(pdf_url: str) -> str:
    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True,
    )
    response = requests.get(
        pdf_url,
        timeout=60,
    )
    response.raise_for_status()
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(
        UPLOAD_DIR,
        filename,
    )
    with open(
        file_path,
        "wb",
    ) as file:
        file.write(response.content)
    return file_path


def upload_and_ingest_pdf(
    pdf_url: str,
):
    file_path = download_pdf_from_url(pdf_url)
    result = ingest_pdf(file_path)
    return result


def save_uploaded_pdf(
    file: UploadFile,
) -> str:
    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True,
    )
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(
        UPLOAD_DIR,
        filename,
    )
    with open(
        file_path,
        "wb",
    ) as output_file:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            output_file.write(chunk)
    return file_path


def save_and_ingest_uploaded_pdf(
    file: UploadFile,
):
    file_path = save_uploaded_pdf(file)
    result = ingest_pdf(file_path)
    return result
