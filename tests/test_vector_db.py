from src.core.db import get_vector_store


def test_vector_store():

    vector_store = get_vector_store()

    docs = vector_store.similarity_search(
        "KYC requirements",
        k=5,
    )

    print("\nVECTOR RESULTS:")
    print("Number of documents:", len(docs))

    for i, doc in enumerate(docs, start=1):

        print(f"\n--- Document {i} ---")
        print("Content:", doc.page_content[:500])
        print("Metadata:", doc.metadata)

    assert len(docs) > 0
