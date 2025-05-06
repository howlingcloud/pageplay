import streamlit as st
import pandas as pd
import pdfplumber
import re

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
                else:
                    st.warning(f"Could not extract text from page {page.page_number}")

        if not text_lines:
            st.error("No extractable text found in the PDF.")
            st.stop()

        # Initialize
        parsed_shots = []
        current_scene = ""
        scene_description = ""
        location = ""
        time_of_day = ""
        shot_counter = 1
        i = 0

        while i < len(text_lines):
            line = text_lines[i].strip()

            # Scene heading
            if re.match(r'^(INT\.|EXT\.)', line):
                current_scene = line
                scene_description = ""
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
                    "Scene Description": scene_description.strip(),
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
                shot_counter += 1
                continue

            # Action or scene body text
            elif line:
                sound = ""
                if "SOUND OF" in line.upper() or any(word in line.upper() for word in ["WHOOSH", "BOOM", "SCREECH", "ECHO", "SCREAM", "CLICK"]):
                    sound = line

                props = re.findall(r'\b[A-Z]{2,}\b', line)
                props_str = "\n".join(set(props)) if props else ""

                scene_description += line + " "

                shot_data = {
                    "Scene Description": scene_description.strip(),
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

        # Output as transposed table with shots as columns
        if parsed_shots:
            df = pd.DataFrame(parsed_shots)
            timeline_df = df.set_index("Shot").T
            st.success("Parsing complete!")
            st.dataframe(timeline_df, use_container_width=True)

            csv = timeline_df.to_csv().encode('utf-8')
            st.download_button("Download CSV", csv, "pageplay_timeline.csv", "text/csv", key="download_csv")
        else:
            st.warning("No valid content was parsed.")
