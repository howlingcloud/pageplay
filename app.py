import streamlit as st
import pandas as pd
import pdfplumber
import re
import numpy as np

st.set_page_config(page_title="PagePlay", layout="wide")
st.title("🎮 PagePlay")
st.subheader("Upload a screenplay and generate a shot-level timeline.")

# --- Initialize session state ---
st.session_state.setdefault("vector_index", None)
st.session_state.setdefault("chunk_metadata", [])
st.session_state.setdefault("instruction_index", None)
st.session_state.setdefault("instruction_metadata", [])

# --- Load IMSDb script vector DB ---
@st.cache_resource
def load_vector_db():
    from datasets import load_dataset
    from sentence_transformers import SentenceTransformer
    import faiss

    dataset = load_dataset("aneeshas/imsdb-genre-movie-scripts")['train']
    model = SentenceTransformer('all-MiniLM-L6-v2')

    text_chunks = []
    metadata = []

    for item in dataset:
        script = item.get('script')
        if not script:
            continue

        lines = script.splitlines()
        for line in lines:
            if line.strip():
                text_chunks.append(line.strip())
                metadata.append({
                    "text": line.strip(),
                    "movie": item.get('title', 'Unknown'),
                    "genre": item.get('genre', 'Unknown')
                })

    if not text_chunks:
        st.warning("No valid script lines were found in the dataset.")
        return None, []

    embeddings = model.encode(text_chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1]()
