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
    model = "gemini-2.0-flash"

    prompt = (
        f"""
        You are a compliance assistant. Compare the following user document chunk to the reference clauses below. 
        Identify what is the type of ADGM(Abu Dhabi Global Market) document the user has sent (for example, application form, mou) and also identify what is the user trying to do, for example, company formation, employment contract etc etc. What other documents does the user need to provide to complete the process? 

        
        For example, if a user wants to form a company, they will need the following documents:
        1. Articles of Association
        2. Memorandum of Association
        3. Board Resolution
        4. Shareholder Resolution
        5. Incorporation Application Form
        6. UBO Declaration form
        7. Register of Members and Directors
        8. Change of Registered Address Notice
        

        Be concise and specific.\n\n
        User Document Chunk:\n{user_chunk}\n\n
        Reference Clauses:\n{references}\n\n

        Identify any compliance issues, missing elements or documents such as these:

        Red Flag Detection Features
            • Invalid or missing clauses
            • Incorrect jurisdiction (e.g., referencing UAE Federal Courts instead of ADGM)
            • Ambiguous or non-binding language
            • Missing signatory sections or improper formatting
            • Non-compliance with ADGM-specific templates
            • Missing documents

        So you must identify missing documents, issues in the user documents, their severity and your suggestion to fix it.

        Your answer must STRICTLY be in json format
        For example:
            {{
                "process": "Company Incorporation",
                "documents_uploaded": 4,
                "required_documents": 5,
                "missing_document": "Register of Members and Directors",
                "issues_found": 
                [
                    {{
                        "document": "Articles of Association",
                        "section": "Clause 3.1",
                        "issue": "Jurisdiction clause does not specify ADGM",
                        "severity": "High",
                        "suggestion": "Update jurisdiction to ADGM Courts."
                    }}
                ]
            }}
        """



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
