import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv() 

# Initialize ChromaDB client and collection
chroma_client = chromadb.Client(Settings())
collection = chroma_client.get_or_create_collection("ai_assistant_docs")

# Load embedding model
EMBED_MODEL = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBED_MODEL, device='cpu')

# Store document chunks
# Each chunk is stored with type: 'doc' or 'qa', and metadata

def store_document_chunks(chunks, source="uploaded_file"):
    chunks = chunks[:20]  # Try with just 20 for now
    st.info("Embedding document chunks, please wait...")
    print("Embedding document chunks...")
    embeddings = embedder.encode(chunks).tolist()
    print("Embedding done.")
    st.success("Embedding done.")
    ids = [f"doc_{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"type": "doc", "source": source}] * len(chunks)
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

# Store Q&A

def store_qa(question: str, answer: str):
    qa_text = f"Q: {question}\nA: {answer}"
    embedding = embedder.encode([qa_text])[0].tolist()
    collection.add(ids=[f"qa_{hash(qa_text)}"], embeddings=[embedding], documents=[qa_text], metadatas=[{"type": "qa"}])

# Retrieve relevant context for a query

def retrieve_context(query: str, top_k=3) -> str:
    query_emb = embedder.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_emb], n_results=top_k)
    docs = results.get("documents", [[]])[0]
    return "\n---\n".join(docs)

