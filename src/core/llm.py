import os
import cohere
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(
    temperature: float = 0,
) -> ChatOpenAI:
    model = os.getenv("OPENAI_MODEL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not model:
        raise ValueError("OPENAI_MODEL is missing.")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
    )


def get_cohere_client():
    return cohere.Client(os.getenv("COHERE_API_KEY"))
