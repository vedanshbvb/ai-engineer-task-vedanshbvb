import streamlit as st
import os
import sys
from pathlib import Path

# Ensure backend is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag_pipeline import review_documents, highlight_and_comment_docx

st.set_page_config(page_title="Corporate Agent", layout="wide")

st.title("📄 Corporate Agent")
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

        # Placeholder for status updates
        status = st.empty()
        status.info("🔍 Reviewing documents...")

        # Step 1: Review documents
        result = review_documents(filepaths)
        status.info("✅ Issues identified, editing documents...")

        # Placeholder for downloads ABOVE issues
        download_placeholder = st.container()

        # Step 2: Process DOCX files for highlighting & commenting
        reviewed_files = []
        if isinstance(result, dict) and result.get("issues_found"):
            for filepath in filepaths:
                if filepath.lower().endswith(".docx"):
                    reviewed_path = os.path.join(
                        "data", "raw", "uploaded", f"reviewed_{os.path.basename(filepath)}"
                    )

                    filename_no_ext = Path(filepath).stem.lower()

                    file_issues = [
                        i for i in result["issues_found"]
                        if filename_no_ext in i.get("document", "").replace(" ", "_").lower()
                        or i.get("document", "").lower() in filename_no_ext
                    ]

                    has_update = highlight_and_comment_docx(filepath, reviewed_path, file_issues)

                    if has_update:
                        reviewed_files.append(reviewed_path)

        # Step 3: Show download buttons (above issues)
        if reviewed_files:
            with download_placeholder:
                st.subheader("📥 Download Edited Files")
                for reviewed_path in reviewed_files:
                    with open(reviewed_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download Reviewed {os.path.basename(reviewed_path)}",
                            data=f,
                            file_name=os.path.basename(reviewed_path),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )

        # Step 4: Issue Report
        if isinstance(result, dict) and result.get("issues_found"):
            issues = result["issues_found"]

            # Count by severity
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

        # Step 5: Show full detected issues dictionary
        st.subheader("Detected Issues & Suggestions (Full JSON)")
        st.json(result)

        status.info("✅ Your documents have been edited and are ready for download.")
