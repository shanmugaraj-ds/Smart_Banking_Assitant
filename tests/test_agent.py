from src.api.v1.agents.agents import invoke


def test_rag_query():
    question = "Explain KYC requirements."
    result = invoke(question)
    print("\nRAG RESULT:")
    print(result)
    assert result["query_type"] == "rag"
    assert result["answer"]


def test_sql_query():
    question = "Show my account balance."
    result = invoke(question)
    print("\nSQL RESULT:")
    print(result)
    assert result["query_type"] == "sql"
    assert result["answer"]


def test_hybrid_query():
    question = "Show my loan balance and explain " "the foreclosure policy."
    result = invoke(question)
    print("\nHYBRID RESULT:")
    print(result)
    assert result["query_type"] == "hybrid"
    assert result["answer"]
