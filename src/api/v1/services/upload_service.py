import os
import tempfile
from fastapi import UploadFile
from src.ingestion.ingestion import ingest_pdf


async def upload_and_ingest_pdf(
    file: UploadFile,
):
    if not file.filename:
        raise ValueError("No file was provided.")
    if not file.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty.")
    print(f"Received PDF: {file.filename}")
    print(f"PDF size: {len(pdf_bytes)} bytes")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name
        print(f"Temporary PDF: {temp_path}")
        result = ingest_pdf(temp_path)
        return {
            "status": "success",
            "message": ("PDF uploaded and ingested successfully."),
            "file_name": file.filename,
            "pages": result["pages"],
            "chunks": result["chunks"],
            "embeddings": result["embeddings"],
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print("Temporary PDF removed.")
