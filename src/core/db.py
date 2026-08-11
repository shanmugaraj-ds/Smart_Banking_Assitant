import os
import psycopg
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_RAG_CONNECTION = os.getenv("PG_VECTOR_CONNECTION_STRING")
PG_RDBMS_CONNECTION = os.getenv("PG_RDBMS_CONNECTION_STRING")
SQL_DATABASE_URI = os.getenv("SQL_DATABASE_URI")


def get_embeddings():
    return OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )


def get_vector_engine() -> Engine:
    if not PG_RAG_CONNECTION:
        raise ValueError("PG_VECTOR_CONNECTION_STRING is not set.")
    return create_engine(PG_RAG_CONNECTION)


def get_connection():
    if not PG_RAG_CONNECTION:
        raise ValueError("PG_VECTOR_CONNECTION_STRING is not set.")
    return psycopg.connect(PG_RAG_CONNECTION)


def initialize_smart_banking_db():
    engine = get_vector_engine()
    with engine.begin() as conn:
        # pgvector
        conn.execute(text("""
                CREATE EXTENSION IF NOT EXISTS vector;
            """))
        # UUID generation
        conn.execute(text("""
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
            """))
        # Main RAG table
        conn.execute(text("""
                CREATE TABLE IF NOT EXISTS smart_banking_chunks (
                    id UUID PRIMARY KEY
                        DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    embedding vector(1536) NOT NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    search_vector TSVECTOR
                );
            """))
        # FTS trigger function
        conn.execute(text("""
                CREATE OR REPLACE FUNCTION
                update_smart_banking_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector :=
                        to_tsvector(
                            'english',
                            COALESCE(NEW.content, '')
                        );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))
        # Trigger
        conn.execute(text("""
                DROP TRIGGER IF EXISTS
                smart_banking_chunks_search_vector_trigger
                ON smart_banking_chunks;
            """))
        conn.execute(text("""
                CREATE TRIGGER
                smart_banking_chunks_search_vector_trigger
                BEFORE INSERT OR UPDATE OF content
                ON smart_banking_chunks
                FOR EACH ROW
                EXECUTE FUNCTION
                update_smart_banking_search_vector();
            """))
        # Vector index
        conn.execute(text("""
                CREATE INDEX IF NOT EXISTS
                idx_smart_banking_chunks_embedding
                ON smart_banking_chunks
                USING hnsw (embedding vector_cosine_ops);
            """))
        # FTS index
        conn.execute(text("""
                CREATE INDEX IF NOT EXISTS
                idx_smart_banking_chunks_fts
                ON smart_banking_chunks
                USING GIN(search_vector);
            """))
    print("Smart Banking DB schema initialized successfully.")


def get_sql_database() -> SQLDatabase:
    if not SQL_DATABASE_URI:
        raise ValueError("SQL_DATABASE_URI is not set.")
    return SQLDatabase.from_uri(
        SQL_DATABASE_URI,
        include_tables=[
            "accounts",
            "card_transactions",
            "credit_cards",
            "fixed_deposits",
            "transactions",
            "loan_accounts",
        ],
    )
