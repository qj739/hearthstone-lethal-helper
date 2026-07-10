#!/usr/bin/env python3
"""从 PNG 生成 Windows 多尺寸 .ico（供 PyInstaller 使用）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "assets" / "hs_lethal_helper_icon.png"
ICO = ROOT / "assets" / "hs_lethal_helper.ico"

ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    if not PNG.is_file():
        raise SystemExit(f"找不到源图: {PNG}")
    img = Image.open(PNG).convert("RGBA")
    # Pillow 会按 sizes 自动生成各尺寸图层
    img.save(ICO, format="ICO", sizes=ICON_SIZES)
    print(f"已写入 {ICO} ({ICO.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
