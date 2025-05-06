# app.py

from dotenv import load_dotenv, find_dotenv
import os
import streamlit as st
import openai

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
)
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ChatVectorDBChain


def load_documents(uploaded_files):
    os.makedirs("uploads", exist_ok=True)
    docs = []
    for u in uploaded_files:
        path = os.path.join("uploads", u.name)
        with open(path, "wb") as f:
            f.write(u.getbuffer())

        if u.type == "application/pdf":
            loader = PyPDFLoader(path)
        elif u.type.startswith("application/vnd.openxmlformats"):
            loader = UnstructuredWordDocumentLoader(path)
        else:
            loader = TextLoader(path, encoding="utf-8")

        try:
            docs.extend(loader.load())
        except Exception as e:
            st.warning(f"⚠️ Could not load {u.name}: {e}")

    return docs


def main():
    st.set_page_config(page_title="📚 Doc-QA + Chat")
    st.title("📚 Document QA + Chat")

    # ─── Load .env & debug ────────────────────────────────────────
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path, override=True)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.error(
            "❌ Missing `OPENAI_API_KEY`. Create a `.env` alongside this file with:\n\n"
            "`OPENAI_API_KEY=sk-<your-full-key-here>`"
        )
        st.stop()

    openai.api_key = api_key

    # ─── Uploader ────────────────────────────────────────────────
    uploads = st.file_uploader(
        "📄 Upload PDF, DOCX or TXT",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
    )
    if not uploads:
        st.info("Please upload at least one document to get started.")
        return

    # ─── Load & split ────────────────────────────────────────────
    docs = load_documents(uploads)
    if not docs:
        st.error("❌ No text could be extracted from your uploads.")
        return
    st.write(f"✅ Loaded {len(docs)} pages from {len(uploads)} file(s).")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    if not chunks:
        st.error("❌ Couldn’t split text into chunks.")
        return
    st.write(f"✅ Split into {len(chunks)} chunks.")

    # ─── Build / load vector store ────────────────────────────────
    persist_dir = "chroma_db"
    embed_fn = OpenAIEmbeddings(openai_api_key=api_key)

    try:
        if chunks:
            vectordb = Chroma.from_documents(
                chunks, embed_fn, persist_directory=persist_dir
            )
            vectordb.persist()
            st.success("🌱 Built vector store from your documents.")
        else:
            vectordb = Chroma(
                persist_directory=persist_dir, embedding_function=embed_fn
            )
            st.info("📂 Loaded existing vector store.")
    except Exception as exc:
        msg = str(exc)
        if "insufficient_quota" in msg or "429" in msg:
            st.error(
                "❌ You’ve exceeded your OpenAI API quota. Please check your plan "
                "and billing details at https://platform.openai.com/account/billing/overview."
            )
        else:
            st.error(
                "❌ Error initializing embeddings/vector store:\n\n"
                f"{exc}\n\n"
                "Please verify your `OPENAI_API_KEY` is correct and active."
            )
        st.stop()

    # ─── Set up QA + Chat ─────────────────────────────────────────
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=api_key)
    qa_chain = ChatVectorDBChain.from_llm(
        llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
    )

    # ─── Chat UI ──────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    user_q = st.chat_input("Ask a question about your documents…")
    if user_q:
        st.session_state.chat_history.append(("user", user_q))
        with st.chat_message("user"):
            st.write(user_q)

        with st.spinner("🔍 Thinking…"):
            result = qa_chain({"question": user_q})
        answer = result["answer"]

        st.session_state.chat_history.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.write(answer)

        vectordb.add_texts(
            [user_q, answer],
            [{"type": "chat_query"}, {"type": "chat_answer"}],
        )
        vectordb.persist()

        if result.get("source_documents"):
            st.write("#### 📑 Sources")
            for doc in result["source_documents"]:
                src = doc.metadata.get("source", "unknown")
                st.write(f"- {src}")


if __name__ == "__main__":
    main()
