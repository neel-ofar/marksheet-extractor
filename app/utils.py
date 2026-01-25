import base64
import io
import json
from PIL import Image, ImageOps
from groq import Groq
from .models import Extraction


def resize_for_groq(image: Image.Image, max_pixels: int = 25_000_000) -> Image.Image:
    pixels = image.width * image.height
    if pixels > max_pixels:
        scale = (max_pixels / pixels) ** 0.5
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)
    return image


def image_to_base64(image: Image.Image) -> str:
    image = resize_for_groq(image)
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG", quality=82)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def get_llm_result(client: Groq, base64_img: str):
    prompt = """\
Look at this marksheet image.
Extract main info as JSON only.
Fields: name, roll_no, subjects (array of objects), result (Pass/Fail/etc)
For each important field add "confidence": 0.0 to 1.0
Return **only** JSON — nothing else.
Example:
{
  "name": {"value": "Rahul Kumar", "confidence": 0.95},
  "roll_no": {"value": "1234567", "confidence": 0.98},
  "subjects": [
    {"subject": "Math", "obtained": "78", "max": "100"},
    ...
  ],
  "result": {"value": "First Division", "confidence": 0.9}
}
"""
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        },
                    },
                ],
            }
        ],
        temperature=0.3,
        max_tokens=800,
    )

    text = resp.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "error": "Invalid JSON from model",
            "raw": text[:300],
        }
