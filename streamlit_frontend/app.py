# gradio_frontend/app.py  -> now Streamlit
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
        
        # st.info("🔍 Reviewing documents...")
        status = st.empty()
        status.info("🔍 Reviewing documents...")

        result = review_documents(filepaths)

        st.subheader("Detected Issues & Suggestions")
        # st.text_area("Results", result, height=500)
        st.json(result)

        print("\n\n\n\ngemini stuff done")
        status.info("Issues identified")

        print(type(result))
        print(result)

        #only process docx files with issues
        if isinstance(result, dict) and result.get("issues_found"):
            print("###########inside###########")
            for filepath in filepaths:

                print("-------------------------------------------------------------------")
                print(f"working for {filepath}")

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

                    print(f"{filepath} {reviewed_path} {file_issues}")

                    has_update = highlight_and_comment_docx(filepath, reviewed_path, file_issues)

                    if has_update:
                        with open(reviewed_path, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Download Reviewed {os.path.basename(filepath)}",
                                data=f,
                                file_name=os.path.basename(reviewed_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )

        status.info("Your documents have been edited, with highlighting the problematic part along with comments about how to set it right")



    
