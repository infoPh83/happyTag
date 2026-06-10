#!/usr/bin/env python3
"""
generate_icons.py
Converts TLE_Seal_ClayRed_RGB.svg into:
  - logo/icon.icns  (macOS)
  - logo/icon.ico   (Windows)
  - logo/png/       (all individual PNGs)

Run from the project root or from inside logo/:
  python logo/generate_icons.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── locate the SVG ────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
SVG_PATH   = SCRIPT_DIR / "TLE_Seal_ClayRed_RGB.svg"
PNG_DIR    = SCRIPT_DIR / "png"
ICONSET    = SCRIPT_DIR / "icon.iconset"
ICNS_OUT   = SCRIPT_DIR / "icon.icns"
ICO_OUT    = SCRIPT_DIR / "icon.ico"

if not SVG_PATH.exists():
    sys.exit(f"SVG not found: {SVG_PATH}")

# On macOS with Homebrew, cairo lives in /opt/homebrew/lib — make sure the
# dynamic linker can find it before importing cairosvg.
_homebrew_lib = "/opt/homebrew/lib"
if os.path.isdir(_homebrew_lib):
    existing = os.environ.get("DYLD_LIBRARY_PATH", "")
    if _homebrew_lib not in existing:
        os.environ["DYLD_LIBRARY_PATH"] = (
            f"{_homebrew_lib}:{existing}" if existing else _homebrew_lib
        )

try:
    import cairosvg
except (ImportError, OSError) as exc:
    sys.exit(
        f"cairosvg could not load (Cairo not found?):\n  {exc}\n\n"
        "Install with:  brew install cairo && pip install cairosvg"
    )

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is not installed. Run:  pip install Pillow")

# ── macOS iconset sizes ───────────────────────────────────────────────────────
# Each tuple: (pixel_size, filename_inside_iconset)
ICONSET_SPECS = [
    (16,   "icon_16x16.png"),
    (32,   "icon_16x16@2x.png"),
    (32,   "icon_32x32.png"),
    (64,   "icon_32x32@2x.png"),
    (128,  "icon_128x128.png"),
    (256,  "icon_128x128@2x.png"),
    (256,  "icon_256x256.png"),
    (512,  "icon_256x256@2x.png"),
    (512,  "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]

# Windows ICO sizes
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def svg_to_png(size: int) -> bytes:
    """Render SVG to a square PNG of the given pixel size."""
    return cairosvg.svg2png(
        url=str(SVG_PATH),
        output_width=size,
        output_height=size,
    )


def main():
    # ── prepare directories ───────────────────────────────────────────────────
    PNG_DIR.mkdir(exist_ok=True)
    if ICONSET.exists():
        shutil.rmtree(ICONSET)
    ICONSET.mkdir()

    print(f"SVG source : {SVG_PATH}")
    print(f"Output dir : {SCRIPT_DIR}\n")

    # ── render unique sizes we actually need ──────────────────────────────────
    needed_sizes = sorted(set(s for s, _ in ICONSET_SPECS) | set(ICO_SIZES))
    png_cache: dict[int, Image.Image] = {}

    for size in needed_sizes:
        print(f"  Rendering {size}×{size} …", end=" ", flush=True)
        raw = svg_to_png(size)
        from io import BytesIO
        img = Image.open(BytesIO(raw)).convert("RGBA")
        png_cache[size] = img
        out = PNG_DIR / f"icon_{size}x{size}.png"
        img.save(out, "PNG")
        print(f"saved → {out.name}")

    # ── build macOS iconset ───────────────────────────────────────────────────
    print("\nBuilding iconset …")
    for size, fname in ICONSET_SPECS:
        dst = ICONSET / fname
        png_cache[size].save(dst, "PNG")
        print(f"  {fname}")

    # ── run iconutil (macOS only) ─────────────────────────────────────────────
    if shutil.which("iconutil"):
        print("\nRunning iconutil …")
        result = subprocess.run(
            ["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS_OUT)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  ✓ {ICNS_OUT}")
        else:
            print(f"  iconutil failed: {result.stderr.strip()}")
    else:
        print("\n⚠  iconutil not found — skipping .icns (run on macOS)")

    # ── build Windows .ico (Pillow multi-size) ────────────────────────────────
    print("\nBuilding icon.ico …")
    ico_images = [png_cache[s] for s in ICO_SIZES]
    # Pillow expects sizes as a list of (w, h) tuples via the sizes kwarg
    ico_images[0].save(
        ICO_OUT,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[1:],
    )
    print(f"  ✓ {ICO_OUT}")

    # ── clean up iconset folder ───────────────────────────────────────────────
    shutil.rmtree(ICONSET)
    print(f"\n Done! Generated files in {SCRIPT_DIR}")
    print(f"   icon.icns  → use in macOS .spec:  icon='logo/icon.icns'")
    print(f"   icon.ico   → use in Windows .spec: icon='logo/icon.ico'")


if __name__ == "__main__":
    main()
