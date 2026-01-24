# app/utils.py
import base64
import io
import json
from typing import List

from PIL import Image
from groq import Groq
from pdf2image import convert_from_bytes

from .models import ExtractionResult


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image → base64 JPEG string"""
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def build_vision_prompt() -> str:
    """Central place for the prompt — easy to tune"""
    return """\
You are an expert at reading Indian and international academic marksheets / grade cards.

Extract the following information precisely:

Candidate:
- Full name
- Father's name (if present)
- Mother's name (if present)
- Roll number / Enrollment number
- Registration number (if different)
- Date of birth (normalize to YYYY-MM-DD)
- Year / Session of examination
- Board / University name
- College / School / Institution name

Subjects table (return ALL subjects visible):
- Subject name
- Maximum marks / credits
- Marks obtained
- Grade / Letter grade (if any)

Overall:
- Result (Pass / Fail / Promoted / compartment, etc.)
- Division / Class (First / Second / Third)
- Grade (if overall grade given)
- Percentage (if calculated)
- Total maximum marks
- Total marks obtained

Other:
- Date of issue (YYYY-MM-DD if possible)
- Place of issue

Rules:
- For EVERY field return "confidence" 0.0–1.0 (1.0 = crystal clear & certain, 0.3 = blurry/ambiguous/partial)
- If field is missing → value = "", confidence = 0.0
- Normalize names, dates, numbers consistently
- Return ONLY valid JSON — no extra text, no markdown
- Use this exact schema:

{
  "candidate_details": { ... },
  "subjects": [ ... ],
  "overall": { ... },
  "issue": { ... or null },
  "bounding_boxes": { "name": "top-left", ... } or null,
  "page_count": 1
}

Be extremely accurate — many marksheets have similar layouts but different boards.
"""
    # You can later move this to a separate prompts/ folder if it grows


def call_vision_llm(client: Groq, base64_image: str) -> ExtractionResult:
    """Single image → structured result"""
    prompt = build_vision_prompt()

    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        temperature=0.15,
        max_tokens=2048,
    )

    raw = completion.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
        return ExtractionResult(**data)
    except Exception as e:
        raise ValueError(f"LLM returned invalid JSON: {raw[:200]}... → {str(e)}")


def merge_extraction_results(results: List[ExtractionResult]) -> ExtractionResult:
    """
    Combine results from multiple pages (very simple version)
    In real projects you would do more intelligent merging
    """
    if not results:
        raise ValueError("No pages processed")

    if len(results) == 1:
        return results[0]

    merged = results[0].model_copy(deep=True)
    merged.page_count = len(results)

    # Naive merge: collect all subjects, take first non-empty candidate info
    all_subjects = []
    for r in results:
        all_subjects.extend(r.subjects)

    merged.subjects = all_subjects

    # Keep the candidate info from the first page that has a name
    for r in results:
        if r.candidate_details.name.value.strip():
            merged.candidate_details = r.candidate_details
            break

    # Similar logic could be applied to overall / issue

    return merged


def process_pdf_bytes(pdf_bytes: bytes) -> List[Image.Image]:
    """PDF bytes → list of PIL images"""
    return convert_from_bytes(pdf_bytes)
