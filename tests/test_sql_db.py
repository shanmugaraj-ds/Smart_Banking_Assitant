import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def test_sql_connection():

    conn = psycopg.connect(os.getenv("PG_RDBMS_CONNECTION_STRING"))

    cursor = conn.cursor()

    cursor.execute("SELECT current_database();")

    db_name = cursor.fetchone()

    print("Connected Database:", db_name)

    assert db_name[0] == "core_banking_db"

    cursor.close()
    conn.close()
