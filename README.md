# SOPbot - Clinical Research SOP Q&A System

RAG system for querying Clinical Research Enterprise Standard Operating Procedures.

## What it does

Processes SOP PDFs, creates vector embeddings, and answers questions using Azure OpenAI + Azure AI Search.

## Stack

- Azure OpenAI (GPT-4, text-embedding-3-small)
- Azure AI Search
- Python, Streamlit, PyPDF2

## Structure
```
SOPbot/
├── data/           # PDF documents
├── src/            # Processing, embeddings, search, RAG
├── notebooks/      # Setup notebook
└── app.py          # Streamlit UI
```

## Example queries

- "What is the parking procedure for patients?"
- "How should informed consent be obtained remotely?"
- "Who is responsible for fiscal reporting?"