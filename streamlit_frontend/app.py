# gradio_frontend/app.py  -> now Streamlit
import streamlit as st
import os
import sys


# Ensure backend is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag_pipeline import review_documents

st.set_page_config(page_title="Document Reviewer", layout="wide")

st.title("📄 Document Reviewer")
st.markdown("Upload your **.docx** or **.pdf** files for automated compliance review.")

uploaded_files = st.file_uploader(
    "Upload Documents",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if st.button("Review Documents"):
    if not uploaded_files:
        st.warning("Please upload at least one document.")
    else:
        filepaths = []
        os.makedirs("data/raw/uploaded", exist_ok=True)
        
        for uploaded_file in uploaded_files:
            temp_path = os.path.join("data", "raw", "uploaded", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            filepaths.append(temp_path)
        
        st.info("🔍 Reviewing documents...")
        result = review_documents(filepaths)
        st.subheader("Detected Issues & Suggestions")
        st.text_area("Results", result, height=500)
