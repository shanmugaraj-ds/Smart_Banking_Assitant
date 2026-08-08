from src.api.v1.agents.sql_agents import create_banking_sql_agent

def test_sql_agent():
    agent = create_banking_sql_agent()
    response = agent.invoke({"input": "Show me 5 recent transactions"})
    print("\nResponse:")
    print(response)
    assert response["output"]
 