from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.v1.services.upload_service import (
    upload_and_ingest_pdf,
)

router = APIRouter(
    prefix="/api/v1/upload",
    tags=["Upload"],
)


@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        print("File:", file.filename)
        print("Content Type:", file.content_type)
        result = await upload_and_ingest_pdf(file)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as error:
        print("UPLOAD ERROR:", repr(error))
        raise HTTPException(
            status_code=500,
            detail=f"PDF ingestion failed: {str(error)}",
        )
