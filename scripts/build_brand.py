"""Build the brand images for Home Assistant and HACS from assets/brand.

Run with (needs libcairo, for example `brew install cairo`):

    uv run --with cairosvg --with pillow scripts/build_brand.py

The wordmark uses the font «Helvetica Neue», which comes with macOS. Other
fonts give a slightly different result.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "brand"
OUT = ROOT / "custom_components" / "kraftvakt" / "brand"

LOGO_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 2200 512" width="2200" height="512">
  {defs}
  <g>{icon}</g>
  <text x="552" y="340" fill="{color}"
        font-family="Helvetica Neue, Helvetica, Arial, sans-serif"
        font-weight="700" font-size="250" letter-spacing="-4">Kraftvakt</text>
</svg>
"""


def icon_parts() -> tuple[str, str]:
    """Return (defs, body) of icon.svg without the outer <svg> tag."""
    svg = (SRC / "icon.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    defs = re.search(r"<defs>.*?</defs>", inner, re.S).group(0)
    body = inner.replace(defs, "")
    return defs, body


def render(svg: str, width: int) -> Image.Image:
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=width)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def trim(img: Image.Image) -> Image.Image:
    """Remove the transparent border, since HA wants little space around the motif."""
    return img.crop(img.getchannel("A").getbbox())


def save(img: Image.Image, name: str) -> None:
    path = OUT / name
    img.save(path, optimize=True)
    print(f"{path.relative_to(ROOT)}  {img.width}x{img.height}")


def fit_height(img: Image.Image, height: int) -> Image.Image:
    width = round(img.width * height / img.height)
    return img.resize((width, height), Image.Resampling.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    icon_svg = (SRC / "icon.svg").read_text(encoding="utf-8")

    for size, name in ((256, "icon.png"), (512, "icon@2x.png")):
        img = trim(render(icon_svg, size * 4))
        side = max(img.size)
        square = Image.new("RGBA", (side, side))
        square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        save(square.resize((size, size), Image.Resampling.LANCZOS), name)

    defs, body = icon_parts()
    for prefix, color in (("", "#0F1B3D"), ("dark_", "#F2F5FB")):
        svg = LOGO_TEMPLATE.format(defs=defs, icon=body, color=color)
        (SRC / f"{prefix}logo.svg").write_text(svg, encoding="utf-8")
        img = trim(render(svg, 8800))
        save(fit_height(img, 128), f"{prefix}logo.png")
        save(fit_height(img, 256), f"{prefix}logo@2x.png")


if __name__ == "__main__":
    main()
