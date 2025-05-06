import os
import requests

def ask_llm(question: str, context: str) -> str:
    llm_provider = os.environ.get("LLM_PROVIDER", "ollama")
    if llm_provider == "ollama":
        # Example: Ollama local API
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        payload = {
            "model": os.environ.get("OLLAMA_MODEL", "llama2"),
            "prompt": f"Context: {context}\n\nQuestion: {question}\nAnswer:",
            "stream": False
        }
        response = requests.post(ollama_url, json=payload)
        if response.ok:
            return response.json().get("response", "[No answer from Ollama]")
        return f"[Ollama error: {response.text}]"
    elif llm_provider == "groq":
        # Example: Groq API (replace with actual endpoint and key)
        groq_url = os.environ.get("GROQ_URL")
        groq_key = os.environ.get("GROQ_API_KEY")
        headers = {"Authorization": f"Bearer {groq_key}"}
        payload = {
            "model": os.environ.get("GROQ_MODEL", "mixtral-8x7b-32768"),
            "messages": [
                {"role": "system", "content": f"Context: {context}"},
                {"role": "user", "content": question}
            ]
        }
        response = requests.post(groq_url, headers=headers, json=payload)
        if response.ok:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "[No answer from Groq]")
        return f"[Groq error: {response.text}]"
    else:
        return "[LLM provider not configured]" 