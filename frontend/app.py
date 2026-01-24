import streamlit as st
import requests
import json
from streamlit_confetti import confetti
  # pip install streamlit-confetti for animation

st.set_page_config(page_title="Marksheet Extractor", layout="wide")
st.markdown("<h1 style='text-align: center; color: #FF6347;'>AI Marksheet Extractor 🚀</h1>", unsafe_allow_html=True)
st.markdown("""<style>body {background: linear-gradient(to right, #FF7E5F, #FEB47B);}</style>""", unsafe_allow_html=True)

file = st.file_uploader("Upload Marksheet (JPG/PNG/PDF)", type=["jpg", "png", "pdf"])
api_key = st.text_input("API Key")

if st.button("Extract"):
    with st.spinner("Extracting..."):
        response = requests.post("http://localhost:8000/extract", files={"file": file}, headers={"api_key": api_key})
    if response.status_code == 200:
        st.json(response.json())
        st.balloons()  # Attention-grabber
        confetti.rain()
    else:
        st.error(response.text)
