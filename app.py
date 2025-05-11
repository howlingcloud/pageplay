import streamlit as st
import pandas as pd
import pdfplumber
import re
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

st.set_page_config(page_title="PagePlay", layout="wide")
st.title("🎮 PagePlay")
st.subheader("Upload a screenplay and generate a shot-level timeline.")

# --- Load pretrained script embeddings ---
st.session_state.setdefault("vector_index", None)
st.session_state.setdefault("chunk_metadata", [])

@st.cache_resource
def load_vector_db():
    from datasets import load_dataset
    dataset = load_dataset("aneeshas/imsdb-genre-movie-scripts")['train']
    model = SentenceTransformer('all-MiniLM-L6-v2')

    text_chunks = []
    metadata = []
    for item in dataset:
        lines = item['script'].splitlines()
        for i, line in enumerate(lines):
            if line.strip():
                text_chunks.append(line.strip())
                metadata.append({"text": line.strip(), "movie": item['title'], "genre": item['genre']})

    embeddings = model.encode(text_chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, metadata

if st.button("Load Pretrained Script Vector DB"):
    with st.spinner("Loading script embeddings from Hugging Face dataset..."):
        st.session_state.vector_index, st.session_state.chunk_metadata = load_vector_db()
    st.success("Vector DB loaded and ready to query!")

# --- Utility functions ---
def is_scene_heading(line):
    return bool(re.match(r"^(INT|EXT|INT./EXT|EXT./INT)[.\s]", line.strip()))

def is_transition(line):
    return line.strip().endswith("TO:") or line.strip() in ["FADE IN:", "FADE OUT:"]

def is_sound_cue(line):
    keywords = ['SOUND', 'HEAR', 'ECHO', 'WHOOSH', 'SCREECH', 'BOOM', 'THUNDER']
    return any(kw in line.upper() for kw in keywords)

def is_camera_direction(line):
    keywords = ['WE SEE', 'WE ARE', 'WE MOVE', 'WE FLY', 'CAMERA', 'TRACK', 'ZOOM', 'PAN', 'CRANE', 'STEADICAM', 'LONG LENS', 'OVERHEAD']
    return any(kw in line.upper() for kw in keywords)

def extract_camera_phrase(line):
    for kw in ['WE SEE', 'WE ARE', 'WE MOVE', 'WE FLY', 'CAMERA MOVES', 'TRACKING', 'LONG LENS']:
        if kw in line.upper():
            return kw
    return ""

def extract_art_props(line):
    phrases = re.findall(r'\b(?:[A-Z0-9\-]{2,})(?:\s+[A-Z0-9\-]{2,})*\b', line)
    return "\n".join(set(phrases))

# --- Core Parser ---
def parse_script(text):
    lines = text.splitlines()
    shots = []

    current_shot = {"Shot": 1, "Location": "", "Time of Day": "", "Character": "", "Action": "", "Dialogue": "",
                    "Art": "", "Sound Design": "", "Camera": "", "EDIT": "", "Scene Summary": ""}

    scene_summary = ""
    in_dialogue = False
    last_scene_summary = ""
    last_location = ""
    last_time = ""

    def flush_shot():
        nonlocal current_shot, shots
        if current_shot["Action"].strip() or current_shot["Dialogue"].strip() or current_shot["Character"]:
            current_shot["Scene Summary"] = last_scene_summary
            shots.append(current_shot.copy())
            current_shot["Shot"] += 1
            for key in ["Character", "Action", "Dialogue", "Art", "Sound Design", "Camera", "EDIT"]:
                current_shot[key] = ""

    for line in lines:
        line = line.strip()
        if not line:
            if current_shot["Action"] or current_shot["Dialogue"]:
                flush_shot()
            in_dialogue = False
            continue

        if is_scene_heading(line):
            flush_shot()
            parts = line.split(" - ")
            current_shot["Location"] = parts[0].strip()
            current_shot["Time of Day"] = parts[1].strip() if len(parts) > 1 else ""
            last_location = current_shot["Location"]
            last_time = current_shot["Time of Day"]
            scene_summary = ""
            continue

        if is_transition(line):
            current_shot["EDIT"] = line
            flush_shot()
            continue

        if is_sound_cue(line):
            current_shot["Sound Design"] += line + " "
            continue

        if is_camera_direction(line):
            phrase = extract_camera_phrase(line)
            current_shot["Camera"] += phrase + " "
            remainder = line.replace(phrase, '').strip()
            if remainder:
                current_shot["Action"] += remainder + " "
            continue

        if not scene_summary:
            scene_summary = line
            last_scene_summary = scene_summary

        if not current_shot["Location"]:
            current_shot["Location"] = last_location
        if not current_shot["Time of Day"]:
            current_shot["Time of Day"] = last_time

        if line.isupper() and len(line.split()) <= 5:
            flush_shot()
            current_shot["Character"] = line
            in_dialogue = True
            continue

        if in_dialogue:
            current_shot["Dialogue"] += line + " "
            continue

        art = extract_art_props(line)
        if art:
            current_shot["Art"] += art + "\n"

        current_shot["Action"] += line + " "

    flush_shot()
    return pd.DataFrame(shots)

# --- Streamlit UI ---
uploaded_file = st.file_uploader("Upload your screenplay PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Parsing PDF..."):
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            st.error("No extractable text found in the PDF.")
        else:
            df = parse_script(text)
            df_transposed = df.set_index("Shot").T.reset_index()
            df_transposed.rename(columns={"index": "Field"}, inplace=True)

            st.success("Parsing complete! Timeline below 👇")
            st.dataframe(df_transposed, use_container_width=True)

            csv = df_transposed.to_csv(index=False).encode('utf-8')
            st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv")
