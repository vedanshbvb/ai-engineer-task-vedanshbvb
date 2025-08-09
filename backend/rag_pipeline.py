import os
from typing import List
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import OpenAI  # or Groq if available
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

import tempfile

from docx import Document as DocxDocument
import PyPDF2

VECTORSTORE_PATH = os.path.join("data", "vectorstore")

def load_faiss_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.load_local(VECTORSTORE_PATH, embeddings)

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

def embed_and_compare(user_chunk, retrieved_docs, llm):
    # Compose a prompt for the LLM to compare user chunk with reference docs
    prompt = PromptTemplate(
        input_variables=["user_chunk", "references"],
        template=(
            "You are a compliance assistant. Compare the following user document chunk to the reference clauses below. "
            "Identify any compliance issues, missing elements, or suggestions for improvement. "
            "Be concise and specific.\n\n"
            "User Document Chunk:\n{user_chunk}\n\n"
            "Reference Clauses:\n{references}\n\n"
            "Issues and Suggestions:"
        )
    )
    references = "\n---\n".join([doc.page_content for doc in retrieved_docs])
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"user_chunk": user_chunk, "references": references})

def review_documents(filepaths: List[str]) -> str:
    # Load vectorstore and LLM
    vectorstore = load_faiss_vectorstore()
    llm = OpenAI(temperature=0)  # or use Groq if available

    all_issues = []
    for path in filepaths:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".docx":
            text = extract_text_from_docx(path)
        elif ext == ".pdf":
            text = extract_text_from_pdf(path)
        else:
            continue  # skip unsupported files

        chunks = chunk_text(text)
        for chunk in chunks:
            # Retrieve top 3 relevant reference docs
            retrieved_docs = vectorstore.similarity_search(chunk, k=3)
            issues = embed_and_compare(chunk, retrieved_docs, llm)
            all_issues.append(f"File: {os.path.basename(path)}\nChunk:\n{chunk[:200]}...\n{issues}\n")

    return "\n\n".join(all_issues) if all_issues else "No issues detected or no supported files uploaded."
