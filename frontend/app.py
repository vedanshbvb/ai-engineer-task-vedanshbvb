import gradio as gr
import sys
import os

# Ensure backend is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag_pipeline import review_documents

def process_files(files):
    # files: list of gradio UploadedFile objects
    filepaths = []
    for f in files:
        # Save uploaded files to a temp location
        temp_path = os.path.join("data", "raw", "uploaded", f.name)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "wb") as out:
            out.write(f.read())
        filepaths.append(temp_path)
    # Call backend review function
    result = review_documents(filepaths)
    return result

with gr.Blocks() as demo:
    gr.Markdown("# Document Reviewer\nUpload your .docx or .pdf files for automated review.")
    file_input = gr.File(file_count="multiple", file_types=[".pdf", ".docx"], label="Upload Documents")
    output = gr.Textbox(label="Detected Issues & Suggestions", lines=20)
    submit_btn = gr.Button("Review Documents")
    submit_btn.click(fn=process_files, inputs=file_input, outputs=output)

if __name__ == "__main__":
    demo.launch()
