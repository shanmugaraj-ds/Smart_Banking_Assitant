import streamlit as st
import requests

QUERY_API_URL = "http://127.0.0.1:8000/api/v1/query/"
UPLOAD_API_URL = "http://127.0.0.1:8000/api/v1/upload/"

st.set_page_config(
    page_title="*** Smart Banking Assistant ***",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "upload_status" not in st.session_state:
    st.session_state.upload_status = None

st.title("Smart Banking Assistant")
st.caption(
    "AI-powered banking assistant using LangGraph, "
    "Hybrid RAG, SQL and LLM reasoning."
)
# SIDEBAR - KNOWLEDGE BASE UPLOAD
with st.sidebar:
    st.header("Knowledge Base")
    st.write("Upload a Smart Banking PDF to the RAG knowledge base.")
    st.divider()
    st.subheader("PDF URL")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Select a PDF from your computer.",
    )
    if uploaded_file is not None:
        if st.button(
            "Upload & Ingest PDF",
            use_container_width=True,
        ):
            try:
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf",
                    )
                }
                with st.spinner("Uploading and ingesting PDF..."):
                    response = requests.post(
                        UPLOAD_API_URL,
                        files=files,
                        timeout=300,
                    )
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.upload_status = result
                    st.success("PDF uploaded and ingested successfully.")
                    st.json(result)
                else:
                    st.error(f"Upload failed: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Unable to connect to FastAPI: {e}")
    # Upload Status
    if st.session_state.uploaded_file_name:
        st.divider()
        st.subheader("📌 Current Knowledge Base")
        st.write(f"**File:** " f"{st.session_state.uploaded_file_name}")
    # Clear Chat
    st.divider()
    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()
# DISPLAY CHAT HISTORY
for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role):
        st.markdown(message["content"])
        if role == "assistant" and message.get("query_type"):
            st.caption(f"Query type: " f"{message['query_type'].upper()}")
question = st.chat_input("Ask your banking question...")
# PROCESS QUESTION
if question:
    question = question.strip()
    if not question:
        st.stop()
    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )
    with st.chat_message("user"):
        st.markdown(question)
    # Prepare chat history
    chat_history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in st.session_state.messages
    ]
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    QUERY_API_URL,
                    json={
                        "question": question,
                        "chat_history": chat_history,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get(
                    "answer",
                    "",
                )
                query_type = result.get(
                    "query_type",
                    "",
                )
                citations = result.get(
                    "citations",
                    [],
                )
                confidence_score = result.get(
                    "confidence_score",
                    None,
                )
                if answer:
                    st.markdown(answer)
                else:
                    st.warning("No answer was generated.")
                if query_type:
                    st.caption(f"Query type: " f"{query_type.upper()}")
                if citations:
                    with st.expander("Sources / Citations"):
                        for citation in citations:
                            st.markdown(f"- {citation}")
                if confidence_score is not None:
                    st.caption(f"Confidence: " f"{float(confidence_score):.2f}")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "query_type": query_type,
                        "citations": citations,
                        "confidence_score": confidence_score,
                    }
                )
            except requests.exceptions.Timeout:
                st.error("The request timed out. " "Please try again.")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Unable to connect to the banking "
                    "assistant API. Please make sure "
                    "FastAPI is running."
                )
            except requests.exceptions.HTTPError:
                try:
                    error_detail = response.json()
                except Exception:
                    error_detail = response.text
                st.error(f"API Error: {error_detail}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
