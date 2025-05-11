import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import requests

st.title("🎞️ Shot-by-Shot Pre-Vis Generator")

uploaded_csv = st.file_uploader("Upload your timeline CSV", type="csv")

@st.cache_data
def load_timeline(csv_file):
    df = pd.read_csv(csv_file)
    return df.T.set_index("Field").T

def build_prompt(row):
    parts = []
    if row["Location"]:
        parts.append(f"Scene: {row['Location']}")
    if row["Time of Day"]:
        parts.append(f"Time: {row['Time of Day']}")
    if row["Character"]:
        parts.append(f"Characters: {row['Character']}")
    if row["Action"]:
        parts.append(f"Action: {row['Action']}")
    if row["Art"]:
        parts.append(f"Props: {row['Art']}")
    if row["Camera"]:
        parts.append(f"Camera Direction: {row['Camera']}")
    return ", ".join(parts)

def generate_image(prompt):
    # Hugging Face example (replace with your preferred generator)
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
    headers = {"Authorization": f"Bearer YOUR_HUGGINGFACE_API_TOKEN"}
    response = requests.post(api_url, headers=headers, json={"inputs": prompt})
    return response.content

if uploaded_csv:
    shots = load_timeline(uploaded_csv)
    selected_index = st.selectbox("Choose Shot #", shots.index)

    row = shots.loc[selected_index]
    editable = st.data_editor(row.to_frame("Value"), use_container_width=True)

    custom_prompt = st.text_area("Generated Prompt", value=build_prompt(editable["Value"]), height=120)

    image_input = st.file_uploader("Optional: Upload visual reference (used only for context)", type=["jpg", "png"])

    if st.button("Generate Pre-Vis Image"):
        with st.spinner("Generating image..."):
            image_data = generate_image(custom_prompt)
            img = Image.open(BytesIO(image_data))
            st.image(img, caption=f"Shot {selected_index} Preview", use_column_width=True)
