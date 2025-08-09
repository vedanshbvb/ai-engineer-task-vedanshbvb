import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate

from docx import Document as DocxDocument
import PyPDF2

from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()


VECTORSTORE_PATH = os.path.join("data", "vectorstore")

# ----------------- Load FAISS -----------------
def load_faiss_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # return FAISS.load_local(VECTORSTORE_PATH, embeddings)
    return FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)


# ----------------- Extractors -----------------
def extract_text_from_docx(path):
    doc = DocxDocument(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text_from_pdf(path):
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def chunk_text(text, chunk_size=800, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# ----------------- Gemini Call -----------------
def call_gemini(user_chunk, references):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-1.5-flash"

    prompt = (
        "You are a compliance assistant. Compare the following user document chunk to the reference clauses below. "
        "Identify any compliance issues, missing elements, or suggestions for improvement. "
        "Be concise and specific.\n\n"
        f"User Document Chunk:\n{user_chunk}\n\n"
        f"Reference Clauses:\n{references}\n\n"
        "Issues and Suggestions:"
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]

    response_text = ""
    for chunk in client.models.generate_content_stream(model=model, contents=contents):
        if chunk.text:
            response_text += chunk.text
    return response_text.strip()

# ----------------- Main Review -----------------
def review_documents(filepaths: List[str]) -> str:
    vectorstore = load_faiss_vectorstore()
    all_issues = []

    for path in filepaths:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".docx":
            text = extract_text_from_docx(path)
        elif ext == ".pdf":
            text = extract_text_from_pdf(path)
        else:
            continue  # skip unsupported

        chunks = chunk_text(text)
        for chunk in chunks:
            retrieved_docs = vectorstore.similarity_search(chunk, k=3)
            references = "\n---\n".join([doc.page_content for doc in retrieved_docs])
            issues = call_gemini(chunk, references)
            all_issues.append(f"File: {os.path.basename(path)}\nChunk:\n{chunk[:200]}...\n{issues}\n")

    return "\n\n".join(all_issues) if all_issues else "No issues detected or no supported files uploaded."
