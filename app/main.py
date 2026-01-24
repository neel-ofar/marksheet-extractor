from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
import uvicorn
from groq import Groq
from PIL import Image
import io
import base64
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import os
from typing import List, Optional
from pydantic import BaseModel
import concurrent.futures

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI(title="Marksheet Extractor API")

class Field(BaseModel):
    value: str
    confidence: float

class CandidateDetails(BaseModel):
    name: Field
    father_name: Optional[Field] = None
    mother_name: Optional[Field] = None
    roll_no: Field
    registration_no: Optional[Field] = None
    dob: Optional[Field] = None
    exam_year: Field
    board_university: Field
    institution: Optional[Field] = None

class Subject(BaseModel):
    subject: str
    max_marks: Optional[str] = None
    obtained_marks: Optional[str] = None
    credits: Optional[str] = None
    grade: Optional[str] = None
    confidence: float

class Overall(BaseModel):
    result: str
    grade: Optional[str] = None
    division: Optional[str] = None
    confidence: float

class Issue(BaseModel):
    date: Optional[str] = None
    place: Optional[str] = None
    confidence: float

class ExtractionResponse(BaseModel):
    candidate_details: CandidateDetails
    subjects: List[Subject]
    overall: Overall
    issue: Optional[Issue] = None
    bounding_boxes: Optional[dict] = None  # Bonus: e.g., {"name": "top-left"}

def process_image(image: Image.Image) -> dict:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    prompt = """
    Extract the following from this marksheet image:
    - Candidate details: name, father/mother’s name, roll no, registration no, DOB, exam year, board/university, institution.
    - Subject-wise: list of subjects with max marks/credits, obtained marks/credits, grade.
    - Overall result/grade/division.
    - Issue date/place if present.
    For each field, provide value and confidence (0-1) based on clarity/ambiguity.
    Estimate bounding box regions (e.g., "top-left", "center").
    Output STRICTLY as JSON matching this schema: {candidate_details: {...}, subjects: [...], overall: {...}, issue: {...}, bounding_boxes: {...}}
    Normalize dates to YYYY-MM-DD, marks to numbers where possible.
    If field missing, set value to "" and confidence 0.
    Examples: High confidence for clear print (1.0), low for blurry (0.4).
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}],
        model="llama-3.2-11b-vision-preview",
        temperature=0.1,
        max_tokens=1024,
    )
    try:
        return eval(chat_completion.choices[0].message.content)  # Parse JSON (use json.loads in prod)
    except:
        raise ValueError("Invalid JSON from LLM")

async def process_file(file: UploadFile) -> dict:
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large")
    content = await file.read()
    if file.content_type in ["image/jpeg", "image/png"]:
        images = [Image.open(io.BytesIO(content))]
    elif file.content_type == "application/pdf":
        images = convert_from_bytes(content)
    else:
        raise HTTPException(400, "Invalid file type")

    # Process pages concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_image, images))
    
    # Aggregate (simple merge for multi-page; enhance if needed)
    aggregated = results[0]  # Assume single-page; merge logic for multi
    for res in results[1:]:
        aggregated["subjects"].extend(res["subjects"])
        # Merge other fields logically

    return aggregated

@app.post("/extract", response_model=ExtractionResponse)
async def extract(file: UploadFile = File(...), api_key: str = Header(None)):
    if api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    try:
        result = await run_in_threadpool(lambda: process_file(file))  # Async for concurrency
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/batch_extract")
async def batch_extract(files: List[UploadFile] = File(...), api_key: str = Header(None)):
    if api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    results = []
    for file in files:
        try:
            result = await process_file(file)
            results.append({"filename": file.filename, "extraction": result})
        except:
            results.append({"filename": file.filename, "error": "Processing failed"})
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
