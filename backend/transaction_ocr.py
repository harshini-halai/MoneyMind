import base64
import json
import re
from io import BytesIO
from typing import Any, Dict, List
import urllib.request
import urllib.error

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

ALLOWED_CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Other"]

def extract_text_from_image(image: Image.Image) -> str:
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(2)
    text = pytesseract.image_to_string(image, config="--psm 6")
    return text.strip()

def _image_to_base64(image: Image.Image) -> str:
    buffered = BytesIO()
    image.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def parse_with_vision_model(image: Image.Image) -> List[Dict[str, Any]]:
    base64_image = _image_to_base64(image)
    prompt = (
        "You are an expense parser. Analyze this transaction screenshot and extract all transactions.\n"
        "Return ONLY a valid JSON list of objects without markdown formatting or code blocks.\n"
        "Each object must have these exact keys:\n"
        "- date: YYYY-MM-DD or empty string if unclear\n"
        "- description: sender or receiver or transaction remarks\n"
        "- amount: positive number or 0.0\n"
        "- type: 'expense' or 'income'\n"
        "- category: one of 'Food', 'Travel', 'Shopping', 'Bills', 'Other'\n"
        "- needs_review: true or false\n"
    )

    payload = {
        "model": "qwen2.5vl:3b",
        "prompt": prompt,
        "images": [base64_image],
        "stream": False,
        "format": "json"
    }

    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            raw_text = result.get("response", "").strip()

            raw_text = re.sub(r"^```(?:json)?", "", raw_text, flags=re.MULTILINE)
            raw_text = re.sub(r"```$", "", raw_text, flags=re.MULTILINE).strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "transactions" in parsed:
                parsed = parsed["transactions"]
            if not isinstance(parsed, list):
                parsed = [parsed]

            validated = []
            for item in parsed:
                category = item.get("category", "Other")
                if category not in ALLOWED_CATEGORIES:
                    category = "Other"

                tx_type = item.get("type", "expense").lower()
                if tx_type not in ["expense", "income"]:
                    tx_type = "expense"

                try:
                    amount = float(item.get("amount", 0.0))
                except (ValueError, TypeError):
                    amount = 0.0

                needs_review = bool(item.get("needs_review", False))
                if amount <= 0 or not item.get("date"):
                    needs_review = True

                validated.append({
                    "date": str(item.get("date", "")),
                    "description": str(item.get("description", "transaction")),
                    "amount": amount,
                    "type": tx_type,
                    "category": category,
                    "needs_review": needs_review
                })
            return validated
    except Exception:
        return []

def extract_transactions_from_image(image: Image.Image) -> List[Dict[str, Any]]:
    transactions = parse_with_vision_model(image)
    if transactions:
        return transactions

    ocr_text = extract_text_from_image(image)
    needs_review = True
    found_amount = 0.0

    match = re.search(r"(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]{1,2})?)", ocr_text, re.IGNORECASE)
    if match:
        try:
            found_amount = float(match.group(1))
        except ValueError:
            found_amount = 0.0

    return [{
        "date": "",
        "description": ocr_text.split("\n")[0][:40] if ocr_text else "manual entry needed",
        "amount": found_amount,
        "type": "expense",
        "category": "Other",
        "needs_review": needs_review
    }]