import os

# Tesseract uses several OpenMP threads. On a host that shows many CPU cores but
# gives you only a small slice of CPU (free cloud plans), those threads fight each
# other and reading gets several times slower. One thread is faster there and is
# just as fast on a normal PC. Set before Tesseract starts; you can override it
# by setting OMP_THREAD_LIMIT yourself.
os.environ.setdefault("OMP_THREAD_LIMIT", "1")

import pytesseract  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from PIL import Image, ImageEnhance, ImageOps, ImageStat  # noqa: E402

load_dotenv()

# Set TESSERACT_CMD in .env if tesseract is not on your PATH, e.g. on Windows:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
_tesseract_cmd = os.getenv("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "60"))
TARGET_WIDTH = 1000  # phone-screenshot text stays easy to read at this width
MIN_WIDTH = 800  # narrower images are enlarged: they read much better
DARK_BRIGHTNESS = 110  # average brightness below this = dark mode screenshot


def prepare_image(image: Image.Image) -> Image.Image:
    """Make the image small, grayscale and black-on-white, so reading is fast."""
    image = ImageOps.exif_transpose(image)  # respect phone-photo rotation
    image = ImageOps.grayscale(image)

    if image.width > TARGET_WIDTH:
        # Only ever shrinks. reducing_gap makes shrinking big photos much faster.
        image.thumbnail(
            (TARGET_WIDTH, image.height), Image.Resampling.LANCZOS, reducing_gap=2.0
        )
    elif image.width < MIN_WIDTH:
        scale = TARGET_WIDTH / image.width
        image = image.resize(
            (TARGET_WIDTH, round(image.height * scale)), Image.Resampling.LANCZOS
        )

    # Dark mode (light text on a dark background): flip to black text on white.
    # Tesseract is both faster and more accurate on that.
    if ImageStat.Stat(image).mean[0] < DARK_BRIGHTNESS:
        image = ImageOps.invert(image)

    return ImageEnhance.Contrast(image).enhance(2)


def extract_text_from_image(image: Image.Image) -> str:
    text = pytesseract.image_to_string(
        prepare_image(image), config="--psm 6", timeout=OCR_TIMEOUT_SECONDS
    )
    return text.strip()