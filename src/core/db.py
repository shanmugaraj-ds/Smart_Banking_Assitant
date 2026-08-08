import psycopg
import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()


model = os.getenv("OPENAI_EMBEDDING_MODEL")
api_key = os.getenv("OPENAI_API_KEY")
pg_vector_connection = os.getenv("PG_VECTOR_CONNECTION_STRING")
pg_rdbms_connection = os.getenv("PG_RDBMS_CONNECTION_STRING")
sql_database_url = os.getenv("SQL_DATABASE_URI")


def get_embeddings():
    return OpenAIEmbeddings(model=model, api_key=api_key)


def get_vector_store(collection_name: str = "smart_banking_chunks"):
    return PGVector(
        collection_name=collection_name,
        connection=pg_vector_connection,
        embeddings=get_embeddings(),
        use_jsonb=True,
    )


def get_sql_database() -> SQLDatabase:
    """
    uses read only credentials and connect to rdbms.
    and targets specific tables our agent can access
    """
    if not pg_rdbms_connection:
        raise ValueError("pg_rdbms_connection is not set.")
    else:
        return SQLDatabase.from_uri(
            sql_database_url,
            include_tables=[
                "accounts",
                "card_transactions",
                "credit_cards",
                "fixed_deposits",
                "transactions",
                "loan_accounts",
            ],
        )


# SQLAlchemy Engine for RAG tables
def get_vector_engine() -> Engine:
    """
    SQLAlchemy engine for smart_banking_db.
    Used for:
    - PostgreSQL Full-Text Search
    - Custom SQL queries
    - Future document management
    """
    if not pg_vector_connection:
        raise ValueError("PG_VECTOR_CONNECTION_STRING is not set.")
    return create_engine(pg_vector_connection)


def get_connection():
    return psycopg.connect(pg_rdbms_connection)

