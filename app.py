import streamlit as st
from file_utils import process_files
from llm_client import ask_llm
from vector_store import store_qa, retrieve_context, store_document_chunks

st.title("MVP AI Assistant")

# File uploader
uploaded_files = st.file_uploader("Upload one or more files", accept_multiple_files=True)
if uploaded_files:
    docs = process_files(uploaded_files)
    store_document_chunks(docs)
    st.success(f"Processed and stored {len(docs)} document chunks.")

# Chat interface
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

user_input = st.text_input("Ask a question about your documents:")
if st.button("Send") and user_input:
    # Retrieve context from vector store
    context = retrieve_context(user_input)
    # Ask LLM
    answer = ask_llm(user_input, context)
    # Store Q&A
    store_qa(user_input, answer)
    # Update chat history
    st.session_state['chat_history'].append((user_input, answer))

# Display chat history
for q, a in st.session_state['chat_history']:
    st.markdown(f"**You:** {q}")
    st.markdown(f"**Assistant:** {a}") 