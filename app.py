import streamlit as st
import pandas as pd
import pdfplumber

# PagePlay branding
st.set_page_config(page_title="PagePlay", layout="wide")

st.title("🎬 PagePlay")
st.subheader("Write. Camera. Action.")

# File uploader
uploaded_file = st.file_uploader("Upload your screenplay PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Parsing PDF..."):
        # Extract raw text lines from PDF
        text_lines = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_lines.extend(text.split('\n'))

        # Basic parser demo – replace with your real v1 parser logic later
        parsed_rows = []
        for i, line in enumerate(text_lines[:30]):  # limit for test
            parsed_rows.append({
                "Scene Description": f"Scene {i//5 + 1}",
                "Shot": f"Shot {i + 1}",
                "Shot Description": line,
                "Location": "",
                "Time of Day": "",
                "Character": "",
                "Dialogue": "",
                "Action": line if line.isupper() else "",
                "Sound Design": "",
                "Camera": "",
                "Art/Props": "",
                "Tone": "",
                "EDIT": ""
            })

        df = pd.DataFrame(parsed_rows)
        st.success("Parsing complete!")

        # Display timeline-style shot grid
        st.dataframe(df, use_container_width=True)

        # Download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv")

