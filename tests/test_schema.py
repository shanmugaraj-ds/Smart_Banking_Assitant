import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg.connect(os.getenv("PG_RDBMS_CONNECTION_STRING"))


def test_visible_tables():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT 
            table_schema,
            table_name
        FROM information_schema.tables
        ORDER BY table_schema, table_name;
    """)

    tables = cur.fetchall()

    print("Visible Tables:", tables)

    cur.execute("""
        SELECT 
            schemaname,
            tablename
        FROM pg_catalog.pg_tables;
    """)

    pg_tables = cur.fetchall()

    print("PG Tables:", pg_tables)

    cur.close()
    conn.close()
