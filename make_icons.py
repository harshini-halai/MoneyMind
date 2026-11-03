"""Creates the MoneyMind icons (favicon.ico, PNG icons) inside the frontend folder.

Run from the project root:   python make_icons.py
Needs only Pillow, which the project already uses.
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "frontend"
BIG = 2048  # drawn large, then shrunk, so the edges are smooth


def bezier(p0, p1, p2, p3, steps=80):
    points = []
    for i in range(steps + 1):
        t = i / steps
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
        points.append(
            (
                a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
            )
        )
    return points


def gradient(size):
    """Diagonal blue (#3b82f6) to teal (#14b8a6)."""
    start, end = (0x3B, 0x82, 0xF6), (0x14, 0xB8, 0xA6)
    image = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(image)
    for d in range(2 * size):
        t = d / (2 * size - 1)
        color = tuple(round(start[i] + (end[i] - start[i]) * t) for i in range(3))
        draw.line([(d, 0), (0, d)], fill=color, width=3)
    return image


def draw_icon(rounded):
    size = BIG
    k = size / 64  # the design is made on a 64 x 64 grid
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    mask = Image.new("L", (size, size), 0)
    radius = round(15 * k) if rounded else 0
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    base.paste(gradient(size), (0, 0), mask)

    draw = ImageDraw.Draw(base)
    width = round(5.2 * k)
    white = (255, 255, 255, 255)

    def scaled(points):
        return [(x * k, y * k) for x, y in points]

    def stroke(points):
        # Stamp a filled circle along the path: gives a solid stroke with round
        # ends and no seams, even on the curve.
        pts = scaled(points)
        radius = width / 2
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            length = max(abs(x2 - x1), abs(y2 - y1), 1)
            steps = int(length / 2) + 1
            for i in range(steps + 1):
                t = i / steps
                x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=white)

    stroke([(19, 17.5), (45, 17.5)])
    stroke([(19, 27), (45, 27)])
    curve = bezier((30.5, 17.5), (40, 17.5), (40, 36.5), (30.5, 36.5))
    stroke([(23, 17.5)] + curve + [(23, 36.5), (40, 52)])
    return base


def resized(image, size):
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    rounded = draw_icon(rounded=True)
    square = draw_icon(rounded=False)  # phones round the corners themselves

    resized(square, 180).save(OUT / "apple-touch-icon.png")
    resized(rounded, 192).save(OUT / "icon-192.png")
    resized(rounded, 512).save(OUT / "icon-512.png")

    sizes = [resized(rounded, s) for s in (16, 32, 48)]
    sizes[2].save(
        OUT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=sizes[:2],
    )

    for name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png", "favicon.ico"):
        print(f"{name}: {(OUT / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()