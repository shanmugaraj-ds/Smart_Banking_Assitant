from pydantic import BaseModel


class UploadRequest(BaseModel):
    pdf_url: str


class UploadResponse(BaseModel):
    status: str
    message: str
    file_name: str
    pages: int
    chunks: int
    embeddings: int
