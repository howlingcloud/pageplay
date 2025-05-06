import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="PagePlay", layout="wide")
st.title("🎬 PagePlay")
st.subheader("Upload a screenplay and parse a shot-level timeline.")

# --- Utility functions ---
def is_scene_heading(line):
    return bool(re.match(r"^(INT|EXT|INT./EXT|EXT./INT)[.\s]", line.strip()))

def is_transition(line):
    return line.strip().endswith("TO:") or line.strip() in ["FADE IN:", "FADE OUT:"]

def is_sound_cue(line):
    sound_keywords = ['SOUND', 'HEAR', 'ECHO', 'WHOOSH', 'SCREECH', 'BOOM', 'THUNDER']
    return any(kw in line.upper() for kw in sound_keywords)

def is_camera_direction(line):
    camera_keywords = ['WE SEE', 'WE ARE', 'WE MOVE', 'WE FLY', 'CAMERA', 'TRACK', 'ZOOM', 'PAN', 'CRANE', 'STEADICAM', 'LONG LENS', 'OVERHEAD']
    return any(kw in line.upper() for kw in camera_keywords)

def extract_camera_phrase(line):
    for kw in ['WE SEE', 'WE ARE', 'WE MOVE', 'WE FLY', 'CAMERA MOVES', 'TRACKING', 'LONG LENS']:
        if kw in line.upper():
            return kw
    return ""

def infer_location_from_line(line):
    location_keywords = ['forest', 'jungle', 'beach', 'desert', 'ocean', 'mountain', 'valley', 'cave']
    words = line.lower().split()
    for word in words:
        if word in location_keywords:
            return word.capitalize()
    return ""

def split_into_sentences(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

# --- Parser core ---
def parse_script(text):
    lines = text.splitlines()
    shots = []
    current_shot = {
        "Shot": 1,
        "Location": "",
        "Time of Day": "",
        "Character": "",
        "Action": "",
        "Dialogue": "",
        "Art": "",
        "Sound Design": "",
        "Camera": "",
        "EDIT": "",
        "Scene Summary": ""
    }
    scene_summary_text = ""
    summary_set = False
    last_explicit_location = ""

    def flush_shot():
        nonlocal current_shot, summary_set
        current_shot["Scene Summary"] = scene_summary_text
        shots.append(current_shot.copy())
        current_shot["Shot"] += 1
        for key in ["Character", "Action", "Dialogue", "Art", "Sound Design", "Camera", "EDIT"]:
            current_shot[key] = ""
        summary_set = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if is_scene_heading(line):
            scene_summary_text = ""
            if current_shot["Action"] or current_shot["Dialogue"]:
                flush_shot()
            parts = line.split(" - ")
            current_shot["Location"] = parts[0].strip()
            last_explicit_location = current_shot["Location"]
            current_shot["Time of Day"] = parts[1].strip() if len(parts) > 1 else ""
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

        if not scene_summary_text and not is_camera_direction(line) and not is_sound_cue(line):
            scene_summary_text = line

        if not current_shot["Location"] and last_explicit_location == "":
            inferred = infer_location_from_line(line)
            if inferred:
                current_shot["Location"] = inferred

        if line.isupper() and len(line.split()) <= 5:
            current_shot["Character"] = line
            continue

        if line.startswith("(") and line.endswith(")"):
            current_shot["Dialogue"] += line + " "
            continue

        if any(char.isupper() for char in line) and len(line.split()) <= 7 and not is_scene_heading(line):
            current_shot["Art"] += line + " "
            continue

        if current_shot["Character"]:
            current_shot["Dialogue"] += line + " "
            continue

        # Otherwise treat as action
        sentences = split_into_sentences(line)
        for sentence in sentences:
            if current_shot["Action"]:
                flush_shot()
            current_shot["Action"] = sentence.strip()

    flush_shot()
    return pd.DataFrame(shots)

# --- Streamlit logic ---
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

            st.success("Parsing complete!")
            st.dataframe(df_transposed, use_container_width=True)

            csv = df_transposed.to_csv(index=False).encode('utf-8')
            st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv")
