from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from src.api.v1.services.upload_service import (
    upload_and_ingest_pdf,
    save_and_ingest_uploaded_pdf,
)

router = APIRouter(
    prefix="/api/v1/upload",
    tags=["Upload"],
)


class PDFUploadRequest(BaseModel):
    pdf_url: HttpUrl


@router.post("/")
def upload_pdf(
    request: PDFUploadRequest,
):
    try:
        result = upload_and_ingest_pdf(str(request.pdf_url))
        return {
            "status": "success",
            "upload_type": "url",
            **result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/file")
def upload_pdf_file(
    file: UploadFile = File(...),
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file selected.",
            )
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported.",
            )
        result = save_and_ingest_uploaded_pdf(file)
        return {
            "status": "success",
            "upload_type": "file",
            "filename": file.filename,
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
