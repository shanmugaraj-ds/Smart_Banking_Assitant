import json
import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from src.core.db import (
    get_embeddings,
    get_vector_engine,
    initialize_smart_banking_db,
)
import pymupdf
import pdfplumber
from PIL import Image
from io import BytesIO
from langchain_core.documents import Document

load_dotenv()


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
    for page_number, page in enumerate(pdf):
        images = page.get_images()
        for image_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf.extract_image(xref)
            image_bytes = base_image["image"]
            image_ref = f"{file_path}" f"_page_{page_number}" f"_image_{image_index}"
            image_chunks.append(
                {
                    "content": f"Image found on page {page_number+1}",
                    "image_ref": image_ref,
                    "page": page_number + 1,
                }
            )
    print("Images extracted:", len(image_chunks))
    return image_chunks


def generate_image_caption(image_chunk):
    """
    Future:
    GPT-4o Vision / Gemini Vision
    """
    return "Image contains banking related " "visual information."


def extract_scanned_text(file_path):
    """
    Placeholder OCR pipeline.
    Future:
    pytesseract
    Azure OCR
    AWS Textract
    """
    return []


def ingest_pdf(file_path):
    print("==== INGESTION STARTED ====")
    # Create database/table/indexes automatically
    initialize_smart_banking_db()
    documents = load_document(file_path)
    documents = enrich_metadata(
        documents,
        file_path,
    )
    text_chunks = create_chunks(documents)
    tables = extract_tables(file_path)
    for table in tables:
        text_chunks.append(
            Document(
                page_content=table["content"],
                metadata={
                    "type": "table",
                    "page": table["page"],
                    "table_no": table["table_no"],
                },
            )
        )
    images = extract_images(file_path)
    for image in images:
        caption = generate_image_caption(image)
        text_chunks.append(
            Document(
                page_content=caption,
                metadata={
                    "type": "image",
                    "image_ref": image["image_ref"],
                    "page": image["page"],
                },
            )
        )
    print(
        "Total chunks before embeddings:",
        len(text_chunks),
    )
    store_embeddings(text_chunks)
    print("==== INGESTION COMPLETED ====")
    return {
        "file": os.path.basename(file_path),
        "pages": len(documents),
        "chunks": len(text_chunks),
        "status": "completed",
    }


if __name__ == "__main__":
    ingest_pdf("data/KB_Smart_Banking.pdf")
