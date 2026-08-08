# # 1.Load the pdf
# # 2.Extract the text from the PDF
# # 3.Split the text into chunks
# #   3.1. We can use a simple split method like splitting
# #   3.2. Follow proper chunking stradegy
# #   3.3. Chunk size = x tokens
# #   3.4. chunk overlap = y tokens
# # 4.Create embeddings for the chunks
# #   4.1. choose the embedding model(text-embedding-3-small)
# #   4.2. choose the dimension of the embeddings
# #   4.3. create the embeddings for each chunk
# # 5.Store thw embeddings in a vector database
# #   5.1. our preferred vector db is pgvector
# #   5.2. we have to activate  pgvector extension in our postgres database
# #   5.3. we have to create a table to store the embeddings
# #   5.4. we have the embeddings into the table


import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredWordDocumentLoader,
    PyPDFLoader,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from sqlalchemy import text
from src.core.db import (
    get_vector_engine,
    get_embeddings,
)

load_dotenv()
PG_CONNECTION = os.getenv("PG_VECTOR_CONNECTION_STRING")


def load_document(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".docx" or ext == ".doc":
        loader = UnstructuredWordDocumentLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    return loader.load(), ext


def ingest_pdf(file_path: str):
    docs, ext = load_document(file_path)
    print("Pages: " + str(len(docs)))
    for doc in docs:
        doc.metadata.update(
            {
                "source": file_path,
                "document_name": os.path.basename(file_path),
                "document_extension": ext,
                "page": doc.metadata.get("page", None),
                "category": "smart_banking",
                "last_updated": os.path.getmtime(file_path),
            }
        )
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    print("Chunks created: " + str(len(chunks)))
    if not chunks:
        raise ValueError("No chunks were created from the document.")
    embeddings = get_embeddings()
    texts = [chunk.page_content for chunk in chunks]
    vectors = embeddings.embed_documents(texts)
    print(f"Embeddings created: {len(vectors)}")
    engine = get_vector_engine()
    insert_sql = text("""
        INSERT INTO smart_banking_chunks
        (
            content,
            embedding,
            metadata,
            search_vector
        )
        VALUES
        (
            :content,
            CAST(:embedding AS vector),
            CAST(:metadata AS jsonb),
            to_tsvector(
                'english',
                :content
            )
        )
        """)
    with engine.begin() as conn:
        for chunk, vector in zip(
            chunks,
            vectors,
        ):
            metadata = dict(chunk.metadata)
            conn.execute(
                insert_sql,
                {
                    "content": chunk.page_content,
                    "embedding": str(vector),
                    "metadata": json.dumps(
                        metadata,
                        default=str,
                    ),
                },
            )
    print(f"Stored chunks: {len(chunks)}")
    print("==== Ingestion completed ====")
    return {
        "chunks_created": len(chunks),
        "chunks_stored": len(chunks),
        "document_name": os.path.basename(file_path),
    }


if __name__ == "__main__":
    ingest_pdf("data/KB_Smart_Banking.pdf")
