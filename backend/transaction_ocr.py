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

OCR_TIMEOUT_SECONDS = 30
MIN_WIDTH = 1200  # small screenshots read much better when enlarged


def extract_text_from_image(image: Image.Image) -> str:
    image = ImageOps.exif_transpose(image)  # respect phone-photo rotation
    image = ImageOps.grayscale(image)

    if image.width < MIN_WIDTH:
        scale = MIN_WIDTH / image.width
        image = image.resize(
            (MIN_WIDTH, int(image.height * scale)), Image.Resampling.LANCZOS
        )

    image = ImageEnhance.Contrast(image).enhance(2)
    text = pytesseract.image_to_string(
        image, config="--psm 6", timeout=OCR_TIMEOUT_SECONDS
    )
    return text.strip()