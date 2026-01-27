from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
import io
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import os
from groq import Groq

from app.utils import image_to_base64, get_llm_result
from .models import Extraction

load_dotenv()

app = FastAPI(title="Simple Marksheet Extractor")

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Marksheet Extractor API is running",
        "docs": "/docs"
    }

client = Groq(api_key=os.getenv("GROQ_API_KEY") or "")

if not client.api_key:
    raise RuntimeError("Missing GROQ_API_KEY in .env")

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if file.size > 20 * 1024 * 1024:
        raise HTTPException(400, "File too large")

    bytes_data = await file.read()

    try:
        if "image" in file.content_type:
            img = Image.open(io.BytesIO(bytes_data))
            images = [img]
        elif "pdf" in file.content_type:
            images = convert_from_bytes(bytes_data)
        else:
            raise HTTPException(400, "Only image or PDF allowed")
    except Exception:
        raise HTTPException(400, "Cannot read file")

    # Process only first page for simplicity
    base64_img = image_to_base64(images[0])
    print(f"Number of pages detected: {len(images)}")
    print(f"Base64 length: {len(base64_img)} characters")  # should be several thousand for a real image
    print(f"First 100 chars of base64: {base64_img[:100]}...")

    result_dict = get_llm_result(client, base64_img)

    # Try to make it match our model (best effort)
    try:
        structured = Extraction(**result_dict)
        return structured.model_dump()
    except:
        return result_dict  # return raw if parsing fails
