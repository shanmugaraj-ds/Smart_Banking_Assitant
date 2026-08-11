import json
import os
import time
import pymupdf
import pdfplumber
import base64
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from src.core.db import (
    get_embeddings,
    get_vector_engine,
    initialize_smart_banking_db,
)
from PIL import Image
from io import BytesIO
from langchain_core.documents import Document

load_dotenv()

vision_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL")

COLLECTION_NAME = "smart_banking_chunks"


def initialize_vector_database():
    engine = get_vector_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE EXTENSION IF NOT EXISTS vector;
            """))


def load_document(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print("Pages:", len(documents))
    return documents


def enrich_metadata(documents, file_path):
    for doc in documents:
        doc.metadata.update(
            {
                "source": file_path,
                "document_name": os.path.basename(file_path),
                "category": "smart_banking",
                "uploaded_time": time.time(),
                "page": doc.metadata.get("page"),
                "content_type": "text",
            }
        )
    return documents


def initialize_fts():
    engine = get_vector_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE smart_banking_chunks
            ADD COLUMN IF NOT EXISTS search_vector tsvector;
            """))
        conn.execute(text("""
            UPDATE smart_banking_chunks
            SET search_vector =
            to_tsvector(
                'english',
                content
            )
            WHERE search_vector IS NULL;
            """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS
            idx_smart_banking_search_vector
            ON smart_banking_chunks
            USING GIN(search_vector);
            """))
    print("FTS initialized")


def create_chunks(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(documents)
    print("Chunks created:", len(chunks))
    return chunks


def store_embeddings(chunks):
    engine = get_vector_engine()
    embeddings = get_embeddings()
    texts = [chunk.page_content for chunk in chunks]
    print("Generating embeddings...")
    vectors = embeddings.embed_documents(texts)
    with engine.begin() as conn:
        for chunk, vector in zip(chunks, vectors):
            conn.execute(
                text("""
                    INSERT INTO smart_banking_chunks
                    (
                        content,
                        embedding,
                        metadata
                    )
                    VALUES
                    (
                        :content,
                        CAST(:embedding AS vector),
                        CAST(:metadata AS jsonb)
                    )
                """),
                {
                    "content": chunk.page_content,
                    "embedding": str(vector),
                    "metadata": json.dumps(
                        chunk.metadata,
                        default=str,
                    ),
                },
            )
    print(f"Embeddings created and stored: {len(chunks)}")


def extract_tables(file_path):
    table_documents = []
    with pdfplumber.open(file_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table_no, table in enumerate(tables):
                if not table:
                    continue
                markdown_table = convert_table_to_markdown(table)
                table_documents.append(
                    {
                        "content": markdown_table,
                        "page": page_no + 1,
                        "table_no": table_no + 1,
                    }
                )
    print("Tables extracted:", len(table_documents))
    return table_documents


def convert_table_to_markdown(table):
    header = [str(x) if x else "" for x in table[0]]
    rows = table[1:]
    markdown = "| " + " | ".join(header) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        markdown += "| " + " | ".join(str(x) if x else "" for x in row) + " |\n"
    return markdown


def extract_images(file_path):
    image_chunks = []
    pdf = pymupdf.open(file_path)
    output_dir = "data/images"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    for page_number, page in enumerate(pdf):
        images = page.get_images(full=True)
        for image_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = os.path.join(
                output_dir,
                f"{base_name}_page_{page_number + 1}_image_{image_index + 1}.{image_ext}",
            )
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
            image_chunks.append(
                {
                    "image_path": image_path,
                    "page": page_number + 1,
                    "image_index": image_index + 1,
                }
            )
    pdf.close()
    print("Images extracted:", len(image_chunks))
    return image_chunks


def build_image_url(image_path: str) -> str:
    filename = os.path.basename(image_path)
    return f"/images/{filename}"


def generate_image_caption(image_path):
    """
    Generate a caption for an extracted image using the vision model.
    """
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = vision_client.responses.create(
            model=VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Describe this banking document image "
                                "accurately. Extract any visible text, "
                                "labels, numbers, tables, charts, or "
                                "important visual information."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": (f"data:image/png;base64,{base64_image}"),
                        },
                    ],
                }
            ],
        )
        return response.output_text
    except Exception as e:
        print(f"Vision caption error for {image_path}: {e}")
        return "Image contains banking-related visual information."


def extract_scanned_text(file_path):
    """
    Extract text from scanned PDF pages using Tesseract OCR.
    """
    ocr_documents = []
    pdf = pymupdf.open(file_path)
    for page_number, page in enumerate(pdf):
        existing_text = page.get_text("text").strip()
        # Only OCR pages that contain little/no extractable text
        if len(existing_text) > 50:
            continue
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )
        ocr_text = pytesseract.image_to_string(image).strip()
        if not ocr_text:
            continue
        ocr_documents.append(
            Document(
                page_content=ocr_text,
                metadata={
                    "source": file_path,
                    "document_name": os.path.basename(file_path),
                    "category": "smart_banking",
                    "content_type": "ocr",
                    "page": page_number + 1,
                },
            )
        )
    print("OCR documents:", len(ocr_documents))
    return ocr_documents


def ingest_pdf(file_path):
    print("INGESTION STARTED")
    # Create database/table/indexes automatically
    initialize_smart_banking_db()
    documents = load_document(file_path)
    documents = enrich_metadata(documents, file_path)
    text_chunks = create_chunks(documents)
    tables = extract_tables(file_path)
    for table in tables:
        text_chunks.append(
            Document(
                page_content=table["content"],
                metadata={
                    "source": file_path,
                    "content_type": "table",
                    "page": table["page"],
                },
            )
        )
    images = extract_images(file_path)
    for image in images:
        image_path = image["image_path"]
        caption = generate_image_caption(image_path)
        text_chunks.append(
            Document(
                page_content=caption,
                metadata={
                    "type": "image",
                    "image_path": image_path,
                    "page": image["page"],
                    "image_index": image["image_index"],
                },
            )
        )
    # NEW OCR STEP
    ocr_documents = extract_scanned_text(file_path)
    for ocr_document in ocr_documents:
        ocr_chunks = create_chunks([ocr_document])
        text_chunks.extend(ocr_chunks)
    print("Total chunks before embeddings:", len(text_chunks))
    store_embeddings(text_chunks)
    print("INGESTION COMPLETED")
    return {
        "file": os.path.basename(file_path),
        "pages": len(documents),
        "chunks": len(text_chunks),
        "status": "completed",
    }


if __name__ == "__main__":
    ingest_pdf("data/KB_Smart_Banking.pdf")
