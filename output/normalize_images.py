"""Give every product photo a uniform white background.

The source photos are inconsistent: most (~74) sit on a black backdrop, the rest on
white/light. For the dark-backdrop photos we cut out the garment with `rembg` using
the **BiRefNet** model (a high-accuracy matting network) and composite it onto solid
white. BiRefNet cleanly separates the garment from the backdrop — including the black
triangles trapped between a body and its sleeves and the dark ribbed hems — while
keeping the whole garment, its shadows, and printed designs (e.g. college crests)
intact. No color thresholding or flood-fill is used, so there are no leftover specks.

Photos already on a white/light background are left untouched: matting them risks
dropping a light (ivory/white) garment that has little contrast with a white backdrop.

Originals are backed up to data/products_original/ the first time this runs, and each
run reprocesses from that backup (idempotent, safe to re-run).

Requires (install into the backend venv):
    pip install rembg onnxruntime pillow numpy
The BiRefNet model (~1 GB) downloads to ~/.rembg on first use. Run from hw4:
    backend/.venv/Scripts/python output/normalize_images.py
"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "data" / "products"
BACKUP = ROOT / "data" / "products_original"
WHITE = (255, 255, 255)
DARK_MAX = 45           # a border pixel this dark counts as "dark backdrop"
DARK_FRACTION = 0.25    # process only if at least this much of the border is dark


def _has_dark_backdrop(arr: np.ndarray) -> bool:
    ring = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    return (ring.max(axis=1) < DARK_MAX).mean() >= DARK_FRACTION


def main() -> None:
    if not BACKUP.exists():
        shutil.copytree(PRODUCTS, BACKUP)
        print(f"Backed up originals to {BACKUP}")

    session = new_session("birefnet-general")
    files = sorted(BACKUP.glob("*.jpg"))
    processed = 0
    for i, f in enumerate(files, 1):
        orig = Image.open(f).convert("RGB")
        arr = np.asarray(orig)

        if _has_dark_backdrop(arr):
            cutout = remove(orig, session=session)          # RGBA, backdrop transparent
            canvas = Image.new("RGB", orig.size, WHITE)
            canvas.paste(cutout, mask=cutout.split()[3])    # composite garment on white
            canvas.save(PRODUCTS / f.name, quality=92)
            processed += 1
        else:
            Image.fromarray(arr).save(PRODUCTS / f.name, quality=92)

        if i % 10 == 0 or i == len(files):
            print(f"  {i}/{len(files)} processed")

    print(f"Normalized {len(files)} images: {processed} matted onto white, "
          f"{len(files) - processed} already light and left untouched.")


if __name__ == "__main__":
    main()
