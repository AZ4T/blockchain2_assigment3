from typing import List
from io import BytesIO

# Add imports for file parsing
import PyPDF2
import docx

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file) -> str:
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def process_files(uploaded_files) -> List[str]:
    chunks = []
    for file in uploaded_files:
        filename = file.name.lower()
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(BytesIO(file.read()))
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(BytesIO(file.read()))
        else:
            text = file.read().decode(errors='ignore')
        # Simple chunking: split by 500 chars
        for i in range(0, len(text), 500):
            chunks.append(text[i:i+500])
    return chunks 