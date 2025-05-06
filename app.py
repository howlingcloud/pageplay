import streamlit as st
import pandas as pd
import pdfplumber

# Set up the app layout and title
st.set_page_config(page_title="PagePlay", layout="wide")
st.title("🎬 PagePlay")
st.subheader("Write. Camera. Action.")

# Upload a screenplay PDF
uploaded_file = st.file_uploader("Upload your screenplay PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Parsing PDF..."):
        text_lines = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_lines.extend(text.split('\n'))

        # Basic placeholder parser logic (replace with real parsing logic)
        parsed_rows = []
        for i, line in enumerate(text_lines[:30]):  # Limit to first 30 lines for testing
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

        # Convert to DataFrame and pivot to timeline format
        df = pd.DataFrame(parsed_rows)
        timeline_df = df.set_index("Shot").T  # Transpose so shots are columns

        st.success("Parsing complete!")

        # Show the horizontal timeline grid
        st.dataframe(timeline_df, use_container_width=True)

        # Provide download option
        csv = timeline_df.to_csv()
        st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv")


        # Download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Timeline CSV", csv, "pageplay_timeline.csv", "text/csv")

