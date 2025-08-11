# AI Engineer Task

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/vgbm4cZ0)

## Folder Structure

```
ai-engineer-task-vedanshbvb/
│
├── streamlit_frontend/                          # Gradio UI code
│   ├── app.py                          # Main Gradio app
│   └── __init__.py
│
├── backend/                           # LangChain & RAG logic
│   ├── rag_pipeline_2.py                 # RAG query and document comparison logic
│   ├── doc_ingestion.py                # Script to scrape/download & embed docs
│   ├── __init__.py
│
├── data/                              # Storage for documents & vector DB
│   ├── raw/                            # Downloaded raw docs/webpage text
│   │   ├── webpages/                   # Scraped guidance text
│   │   ├── templates/                  # Official doc templates (.docx, .pdf)
│   ├── processed/                      # Cleaned/converted text
│   └── vectorstore/                    # Saved FAISS/Chroma DB
│
├── requirements.txt                   # Python dependencies
├── README.md
└── Task.pdf                            # The assignment brief
```

## App Overview

This project provides a streamlit-based UI for uploading multiple documents (.docx, .pdf), which are then reviewed by a LangChain-powered RAG pipeline. The backend checks the documents for issues and suggests corrections, leveraging a FAISS vector store for retrieval.

- Upload documents via the Streamlit interface.
- Documents are processed and compared against guidance/templates.
- Detected issues and suggestions are displayed to the user.

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Make the env file
   Add your Gemini API Key to the .env file
   GEMINI_API_KEY =

3. Upload documents to the VectorStore

   Use the following command to automatically scrape the links and upload the data to the vector store
    ```
    python backend/doc_ingestion.py 
    ```

4. Run the app

    ```
    python -m streamlit run streamlit_frontend/app.py
    ```

5. Download the zip of the edited documents
   You can go through them to see where to make changes

   <img src="./media/prompt.png" alt="App Preview" width="350" />



## Common Errors
If you get an error like "None type object not subscriptable", simply reload and review the document again  