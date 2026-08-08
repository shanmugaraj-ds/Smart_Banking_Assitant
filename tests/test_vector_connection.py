import os
from dotenv import load_dotenv

from src.core.db import get_vector_store

load_dotenv()


def test_vector_connection():

    print("\nVECTOR DB:")
    print(os.getenv("PG_VECTOR_CONNECTION_STRING"))

    vector_store = get_vector_store()

    print("\nCollection:")
    print(vector_store.collection_name)
