import streamlit as st
import requests

st.set_page_config(page_title="Marksheet Extractor", page_icon="📄", layout="centered")

st.title("📄 Marksheet Extractor")
st.markdown("### Upload your marksheet → Get instant results")

# ←←← YAHAN APNA BACKEND URL DAAL DO
BACKEND_URL = "https://marksheet-extractor-ciik.onrender.com"

uploaded_file = st.file_uploader("Choose JPG, PNG or PDF", type=["jpg", "png", "pdf"])

if uploaded_file:
    st.image(uploaded_file, caption="Preview", use_container_width=True)

    if st.button("🚀 Extract Now", type="primary", use_container_width=True):
        with st.spinner("AI is reading your marksheet... Please wait (10–60 sec)"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(f"{BACKEND_URL}/extract", files=files, timeout=120)

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Extraction Successful!")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Name", data.get("name", {}).get("value", "—"))
                    col2.metric("Roll No", data.get("roll_no", {}).get("value", "—"))
                    col3.metric("Result", data.get("result", {}).get("value", "—"))

                    if data.get("subjects"):
                        st.subheader("Subjects")
                        st.table(data["subjects"])

                    st.subheader("Full JSON")
                    st.json(data)

                else:
                    st.error(f"Error {response.status_code}")
                    st.json(response.json() if "json" in response.headers.get("content-type", "") else response.text)

            except Exception as e:
                st.error(f"Connection Error: {e}")
                st.info("Check if backend is awake. Try refreshing backend URL once.")

else:
    st.info("👆 Upload a marksheet to start")
