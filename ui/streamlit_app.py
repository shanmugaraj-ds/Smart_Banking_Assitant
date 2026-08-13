import json
import streamlit as st
import requests

QUERY_API_URL = "http://127.0.0.1:8000/api/v1/query/"
QUERY_STREAM_API_URL = "http://127.0.0.1:8000/api/v1/query/stream"
UPLOAD_API_URL = "http://127.0.0.1:8000/api/v1/upload/"

st.set_page_config(
    page_title="Smart Banking Assistant",
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
# SIDEBAR
with st.sidebar:
    st.header("Customer Details")
    account_id = st.text_input(
        "Account ID",
        value="1345367",
        placeholder="Enter account ID",
    )
    st.divider()
    st.header("Knowledge Base")
    st.write("Upload a Smart Banking PDF " "to the RAG knowledge base.")
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
    # Upload status
    if st.session_state.uploaded_file_name:
        st.divider()
        st.subheader("Current Knowledge Base")
        st.write(f"**File:** " f"{st.session_state.uploaded_file_name}")
    # Clear chat
    st.divider()
    if st.button(
        "Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()
for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role):
        st.markdown(message["content"])
        if role == "assistant":
            if message.get("images"):
                st.subheader("Related Images")
                for image_url in message["images"]:
                    st.image(
                        image_url,
                        caption="Related image",
                        use_container_width=True,
                    )
            if message.get("query_type"):
                st.caption("Query type: " f"{message['query_type'].upper()}")
            if message.get("citations"):
                with st.expander("Sources / Citations"):
                    for citation in message["citations"]:
                        st.markdown(f"- {citation}")
            if message.get("confidence_score") is not None:
                st.caption("Confidence: " f"{float(message['confidence_score']):.2f}")
question = st.chat_input("Ask your banking question...")
# PROCESS QUESTION
if question:
    question = question.strip()
    if not question:
        st.stop()
    # User message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )
    with st.chat_message("user"):
        st.markdown(question)
    # Chat history
    chat_history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in st.session_state.messages
    ]
    # Assistant
    with st.chat_message("assistant"):
        try:
            response = requests.post(
                QUERY_STREAM_API_URL,
                json={
                    "question": question,
                    "chat_history": chat_history,
                    "account_id": account_id.strip() if account_id else None,
                },
                stream=True,
                timeout=300,
            )
            response.raise_for_status()
            answer_placeholder = st.empty()
            status_placeholder = st.empty()
            final_result = None
            # Read SSE stream
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if not data:
                    continue
                event = json.loads(data)
                event_type = event.get("type")
                # STATUS
                if event_type == "status":
                    message = event.get(
                        "message",
                        "Processing...",
                    )
                    status_placeholder.info(message)
                # COMPLETE
                elif event_type == "complete":
                    final_result = event
                    status_placeholder.empty()
                    answer = event.get(
                        "answer",
                        "",
                    )
                    if answer:
                        answer_placeholder.markdown(answer)
                    # Images
                    images = event.get(
                        "images",
                        [],
                    )
                    if images:
                        st.subheader("Related Images")
                        for image_url in images:
                            st.image(
                                image_url,
                                caption="Related image",
                                use_container_width=True,
                            )
                    # Query type
                    query_type = event.get(
                        "query_type",
                        "",
                    )
                    if query_type:
                        st.caption("Query type: " f"{query_type.upper()}")
                    # Citations
                    citations = event.get(
                        "citations",
                        [],
                    )
                    if citations:
                        with st.expander("Sources / Citations"):
                            for citation in citations:
                                st.markdown(f"- {citation}")
                    # Confidence
                    confidence_score = event.get("confidence_score")
                    if confidence_score is not None:
                        st.caption("Confidence: " f"{float(confidence_score):.2f}")
                # ERROR
                elif event_type == "error":
                    status_placeholder.empty()
                    st.error(
                        event.get(
                            "message",
                            "Unknown error",
                        )
                    )
            # Save complete assistant response
            if final_result:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": final_result.get(
                            "answer",
                            "",
                        ),
                        "query_type": final_result.get(
                            "query_type",
                            "",
                        ),
                        "citations": final_result.get(
                            "citations",
                            [],
                        ),
                        "confidence_score": (
                            final_result.get(
                                "confidence_score",
                                0,
                            )
                        ),
                        "images": final_result.get(
                            "images",
                            [],
                        ),
                    }
                )
        except requests.exceptions.Timeout:
            st.error("The request timed out. " "Please try again.")
        except requests.exceptions.ConnectionError:
            st.error(
                "Unable to connect to the "
                "banking assistant API. "
                "Please make sure FastAPI "
                "is running."
            )
        except requests.exceptions.HTTPError:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            st.error(f"API Error: {error_detail}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
