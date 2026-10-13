import pytesseract
from PIL import Image, ImageOps, ImageEnhance

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_from_image(image: Image.Image) -> str:
    image = ImageOps.grayscale(image)
    image = ImageEnhance.Contrast(image).enhance(2)
    text = pytesseract.image_to_string(image, config="--psm 6")
    return text.strip()