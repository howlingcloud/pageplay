import streamlit as st
import pandas as pd
import pdfplumber

st.title("📽️ Screen Writer Timeline Parser")
uploaded_file = st.file_uploader("Upload a screenplay PDF", type="pdf")

def parse_pdf(pdf_file):
    parsed_rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line.upper().startswith("INT.") or line.upper().startswith("EXT."):
                    parsed_rows.append({
                        "Shot": f"Scene {len(parsed_rows)+1}",
                        "Scene Description": line,
                        "Location": "INT." if "INT." in line else "EXT.",
                        "Time of Day": "NIGHT" if "NIGHT" in line else "DAY",
                        "Character": "",
                        "Action": "",
                        "Sound Design": "",
                        "Camera": "",
                        "Tone": "",
                        "EDIT": ""
                    })
    return parsed_rows

if uploaded_file is not None:
    parsed_rows = parse_pdf(uploaded_file)

    if parsed_rows:
        df = pd.DataFrame(parsed_rows)
        timeline_df = df.set_index("Shot").T  # Transpose: shots become columns
        st.subheader("📊 Shot Breakdown Timeline")
        st.dataframe(timeline_df)
    else:
        st.warning("No scenes found. Make sure the script is formatted correctly.")
else:
    st.info("Please upload a screenplay PDF.")
