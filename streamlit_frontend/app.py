import streamlit as st
import os
import sys
import shutil
from pathlib import Path
import io
import zipfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.rag_pipeline_2 import review_documents, highlight_and_comment_docx

st.set_page_config(page_title="Corporate Agent", layout="wide")

# Temporary storage for reviewed files (still using static dir for now)
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

st.title("📄 Corporate Agent")
st.markdown("Upload your **.docx** or **.pdf** files for automated compliance review.")

# Session state
if "result" not in st.session_state:
    st.session_state.result = None
if "reviewed_files" not in st.session_state:
    st.session_state.reviewed_files = []

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

        status = st.empty()
        status.info("🔍 Reviewing documents...")

        result = review_documents(filepaths)
        status.info("✅ Issues identified, editing documents...")

        reviewed_files = []
        if isinstance(result, dict) and result.get("issues_found"):
            for filepath in filepaths:
                if filepath.lower().endswith(".docx"):
                    reviewed_path = os.path.join(
                        "data", "raw", "uploaded", f"reviewed_{os.path.basename(filepath)}"
                    )

                    filename_no_ext = Path(filepath).stem.lower()
                    # file_issues = [
                    #     i for i in result["issues_found"]
                    #     if filename_no_ext in i.get("document", "").replace(" ", "_").lower()
                    #     or i.get("document", "").lower() in filename_no_ext
                    # ]

                    # file_issues = [
                    #     i for i in result["issues_found"]
                    #     if filename_no_ext in str(i.get("document") or "").replace(" ", "_").lower()
                    #     or str(i.get("document") or "").lower() in filename_no_ext
                    # ]

                    file_issues = [
                        i for i in result["issues_found"]
                        if i.get("document", "").lower().replace(" ", "") in filename_no_ext.replace(" ", "")
                        or filename_no_ext.replace(" ", "") in i.get("document", "").lower().replace(" ", "")
                    ]



                    highlighted = highlight_and_comment_docx(filepath, reviewed_path, file_issues)

                    if not highlighted:
                        shutil.copy(filepath, reviewed_path)

                    reviewed_files.append(reviewed_path)

                else:
                    # PDFs - just copy them as reviewed (optional)
                    reviewed_path = os.path.join(
                        "data", "raw", "uploaded", f"reviewed_{os.path.basename(filepath)}"
                    )
                    shutil.copy(filepath, reviewed_path)
                    reviewed_files.append(reviewed_path)

        # Save to session state
        st.session_state.result = result
        st.session_state.reviewed_files = reviewed_files
        status.info("✅ Your documents have been processed and are ready for download.")

# Step 1: One-click ZIP download for all reviewed files
if st.session_state.reviewed_files:
    st.subheader("📥 Download All Edited Files")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filepath in st.session_state.reviewed_files:
            zipf.write(filepath, arcname=os.path.basename(filepath))
    zip_buffer.seek(0)

    st.download_button(
        label="⬇️ Download All Reviewed Documents",
        data=zip_buffer,
        file_name="reviewed_documents.zip",
        mime="application/zip"
    )

# Step 2: Issue Report
if st.session_state.result and isinstance(st.session_state.result, dict):
    result = st.session_state.result
    if result.get("issues_found"):
        issues = result["issues_found"]

        severity_counts = {"Low": 0, "Medium": 0, "High": 0}
        severity_map = {"Low": [], "Medium": [], "High": []}

        for issue in issues:
            sev = issue.get("severity", "").capitalize()
            if sev in severity_counts:
                severity_counts[sev] += 1
                severity_map[sev].append(issue)

        st.subheader("📊 Issue Report")
        st.write(
            f"**High Severity Issues:** {severity_counts['High']} | "
            f"**Medium:** {severity_counts['Medium']} | "
            f"**Low:** {severity_counts['Low']}"
        )

        for sev in ["High", "Medium", "Low"]:
            if severity_map[sev]:
                with st.expander(f"{sev} Severity Issues ({severity_counts[sev]})"):
                    for issue in severity_map[sev]:
                        st.markdown(
                            f"**Document:** {issue['document']}  \n"
                            f"**Section:** {issue.get('section', 'N/A')}  \n"
                            f"**Issue:** {issue['issue']}  \n"
                            f"**Suggestion:** {issue['suggestion']}"
                        )
                        st.markdown("---")

    st.subheader("Detected Issues & Suggestions (Full JSON)")
    st.json(st.session_state.result)
