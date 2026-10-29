import os

import pytesseract
from dotenv import load_dotenv
from PIL import Image, ImageEnhance, ImageOps

load_dotenv()

# Set TESSERACT_CMD in .env if tesseract is not on your PATH, e.g. on Windows:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
_tesseract_cmd = os.getenv("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


def extract_text_from_image(image: Image.Image) -> str:
    image = ImageOps.exif_transpose(image)  # respect phone-photo rotation
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(2)
    text = pytesseract.image_to_string(image, config="--psm 6")
    return text.strip()