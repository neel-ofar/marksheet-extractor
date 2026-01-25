import streamlit as st
import requests

st.title("Marksheet Extractor")
st.caption("Make sure backend is running → uvicorn app.main:app")

file = st.file_uploader("Choose marksheet", type=["jpg", "png", "pdf"])

if file:
    st.image(file, caption="Uploaded file preview")

if file and st.button("Extract"):
    with st.spinner("Working..."):
        try:
            resp = requests.post(
                "http://localhost:8000/extract",
                files={"file": (file.name, file.getvalue(), file.type)},  # ← better: explicit filename & content_type
                timeout=90                                               # ← increased to 90 s (vision LLM can be slow)
            )
            resp.raise_for_status()

            st.success("Extraction successful!")
            st.json(resp.json())

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.\nMake sure you started it with:\n`uvicorn app.main:app --reload`")

        except requests.exceptions.HTTPError:
            # Here resp definitely exists
            st.error(f"Backend returned status {resp.status_code}")
            try:
                error_detail = resp.json()
                st.json(error_detail)
            except:
                st.code(resp.text or "No additional details available")

        except requests.exceptions.Timeout:
            st.error("Request timed out. The file may be too large or the model is slow. Try a smaller file.")

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
