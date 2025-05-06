import streamlit as st
import pandas as pd
import pdfplumber
import re

# Configure the Streamlit page
st.set_page_config(page_title="PagePlay", layout="wide")
st.title("🎬 PagePlay")
st.subheader("Write. Camera. Action.")

uploaded_file = st.file_uploader("Upload your screenplay PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Parsing PDF..."):
        text_lines = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_lines.extend(text.split('\n'))

        # Initialize parsing
        parsed_shots = []
        current_scene = ""
        location = ""
        time_of_day = ""
        shot_counter = 1
        i = 0

        while i < len(text_lines):
            line = text_lines[i].strip()

            # Scene heading
            if re.match(r'^(INT\.|EXT\.)', line):
                current_scene = line
                location_match = re.match(r'^(INT\.|EXT\.)\s+(.+?)\s*-\s*(\w+)', line)
                if location_match:
                    location = location_match.group(2).strip()
                    time_of_day = location_match.group(3).strip()
                i += 1
                continue

            # Character + Dialogue
            elif line.isupper() and 1 <= len(line) <= 30:
                character = line
                is_vo = "(V.O.)" in character or "(O.S.)" in character
                dialogue = ""
                i += 1
                while i < len(text_lines) and text_lines[i].strip() and not text_lines[i].isupper():
                    dialogue += text_lines[i].strip() + " "
                    i += 1

                shot_data = {
                    "Scene Description": current_scene,
                    "Shot": f"Shot {shot_counter}",
                    "Shot Description": dialogue.strip(),
                    "Location": location,
                    "Time of Day": time_of_day,
                    "Character": character,
                    "Dialogue": dialogue.strip(),
                    "Action": "" if not is_vo else dialogue.strip(),
                    "Sound Design": "",
                    "Camera": "",
                    "Art/Props": "",
                    "Tone": "",
                    "EDIT": ""
                }

                parsed_shots.append(shot_data)
                if not is_vo:
                    shot_counter += 1
                continue

            # Action or other lines
            elif line:
                # Sound detection
                sound = ""
                if "SOUND OF" in line.upper() or any(word in line.upper() for word in ["WHOOSH", "BOOM", "SCREECH", "ECHO"]):
                    sound = line

                # Prop detection (all caps words longer than 1 char)
                props = re.findall(r'\b[A-Z]{2,}\b', line)
                props_str = "\n".join(set(props)) if props else ""

                shot_data = {
                    "Scene Description": current_scene,
                    "Shot": f"Shot {shot_counter}",
                    "Shot Description": line,
                    "Location": location,
                    "Time of Day": time_of_day,
                    "Character": "",
                    "Dialogue": "",
                    "Action": line,
                    "Sound Design": sound,
                    "Camera": "",
                    "Art/Props": props_str,
                    "Tone": "",
                    "EDIT": ""
                }

                parsed_shots.append(shot_data)
                shot_counter += 1
                i += 1
                continue

            else:
                i += 1

if 'timeline_df' in locals():
    st.success("Parsing complete!")
    st.dataframe(timeline_df, use_container_width=True)

    csv = timeline_df.to_csv().encode('utf-8')
    st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv", key="download_csv")

# After parsing and populating parsed_shots
df = pd.DataFrame(parsed_shots)
timeline_df = df.set_index("Shot").T

st.success("Parsing complete!")
st.dataframe(timeline_df, use_container_width=True)

csv = timeline_df.to_csv().encode('utf-8')
st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv", key="download_csv")





