"""Generate the Windows app icon used by the PyInstaller build."""

from __future__ import annotations

import argparse
from pathlib import Path


def create_icon(output_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required to generate the Windows icon. "
            "Install the build extra with: uv sync --extra build-windows"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    base_size = 256
    image = Image.new("RGBA", (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (18, 26, 238, 230), radius=54, fill=(14, 116, 115, 255), outline=(7, 47, 54, 255), width=8
    )
    draw.rounded_rectangle((48, 68, 208, 196), radius=30, fill=(247, 242, 230, 255))
    draw.arc((66, 88, 190, 170), start=0, end=180, fill=(7, 47, 54, 255), width=12)
    draw.line((82, 132, 82, 164), fill=(7, 47, 54, 255), width=12)
    draw.line((174, 132, 174, 164), fill=(7, 47, 54, 255), width=12)
    draw.arc((82, 126, 174, 202), start=0, end=180, fill=(7, 47, 54, 255), width=10)

    for x, height in [(104, 34), (122, 58), (140, 44), (158, 70)]:
        y_mid = 132
        draw.rounded_rectangle(
            (x, y_mid - height // 2, x + 8, y_mid + height // 2), radius=4, fill=(244, 173, 78, 255)
        )

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    image.save(output_path, format="ICO", sizes=sizes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="Output .ico path")
    args = parser.parse_args()

    create_icon(args.out)


if __name__ == "__main__":
    main()
