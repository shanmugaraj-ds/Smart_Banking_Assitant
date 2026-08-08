from src.api.v1.agents.agents import banking_agent


class SQLService:
    def __init__(self):
        self.agent = banking_agent()

    def execute_query(self, question: str):
        response = self.agent.invoke({"input": question})
        return {"answer": response["output"]}
