"""Chuyển toàn bộ bản vẽ PDF trong FICHIER PROMPT sang PNG + sinh manifest.csv.

Cách dùng:
    python scripts/pdf_to_png.py                    # 300 DPI, grayscale
    python scripts/pdf_to_png.py --dpi 200
    python scripts/pdf_to_png.py --max-side 2048    # thu nhỏ cạnh dài nhất
    python scripts/pdf_to_png.py --force            # ghi de anh da co
"""

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "FICHIER PROMPT"
OUT_DIR = ROOT / "dataset" / "images"
MANIFEST = ROOT / "dataset" / "manifest.csv"


def slug(text):
    """Bo dau, chuan hoa ve [A-Z0-9_] de ten file an toan tren moi he thong."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text.upper()


def ink_ratio(pix):
    """Ty le pixel khong phai nen trang. Dung de phat hien trang trong/hong."""
    data = pix.samples
    dark = sum(1 for b in data[::37] if b < 200)  # lay mau thua cho nhanh
    return dark / max(1, len(data[::37]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--max-side", type=int, default=0, help="0 = giu nguyen")
    ap.add_argument("--color", action="store_true", help="giu mau, mac dinh grayscale")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not SRC_DIR.is_dir():
        sys.exit(f"Khong tim thay thu muc nguon: {SRC_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(SRC_DIR.rglob("*.pdf"))
    if not pdfs:
        sys.exit(f"Khong co PDF nao trong {SRC_DIR}")

    colorspace = fitz.csRGB if args.color else fitz.csGRAY
    rows = []
    errors = []
    skipped = 0

    for pdf_path in pdfs:
        rel = pdf_path.relative_to(SRC_DIR)
        parts = rel.parts
        famille = parts[0]
        sous_famille = parts[1] if len(parts) > 2 else ""
        stem = pdf_path.stem

        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:  # pdf hong
            errors.append((str(rel), f"open: {exc}"))
            continue

        with doc:
            for pno, page in enumerate(doc, start=1):
                name_parts = [slug(famille)]
                if sous_famille:
                    name_parts.append(slug(sous_famille))
                name_parts.append(slug(stem))
                base = "__".join(name_parts)
                if doc.page_count > 1:
                    base += f"__p{pno}"
                png_path = OUT_DIR / f"{base}.png"

                if png_path.exists() and not args.force:
                    skipped += 1
                    continue

                try:
                    pix = page.get_pixmap(dpi=args.dpi, colorspace=colorspace)
                    if args.max_side and max(pix.width, pix.height) > args.max_side:
                        scale = args.max_side / max(pix.width, pix.height)
                        mat = fitz.Matrix(args.dpi / 72 * scale, args.dpi / 72 * scale)
                        pix = page.get_pixmap(matrix=mat, colorspace=colorspace)
                    pix.save(png_path)
                except Exception as exc:
                    errors.append((str(rel), f"page {pno}: {exc}"))
                    continue

                rows.append(
                    {
                        "image": png_path.name,
                        "pdf_path": str(rel).replace("\\", "/"),
                        "famille": famille,
                        "sous_famille": sous_famille,
                        "drawing_name": stem,
                        "page": pno,
                        "width": pix.width,
                        "height": pix.height,
                        "dpi": args.dpi,
                        "ink_ratio": round(ink_ratio(pix), 4),
                    }
                )

    # Manifest: gop voi ban cu neu chay lai mot phan
    existing = {}
    if MANIFEST.exists() and not args.force:
        with MANIFEST.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                existing[r["image"]] = r
    for r in rows:
        existing[r["image"]] = r

    fieldnames = [
        "image", "pdf_path", "famille", "sous_famille", "drawing_name",
        "page", "width", "height", "dpi", "ink_ratio",
    ]
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for image in sorted(existing):
            w.writerow(existing[image])

    print(f"PDF quet duoc      : {len(pdfs)}")
    print(f"PNG moi xuat       : {len(rows)}")
    print(f"Bo qua (da co)     : {skipped}")
    print(f"Loi                : {len(errors)}")
    for rel, msg in errors[:20]:
        print(f"  ! {rel} -> {msg}")
    print(f"Manifest           : {MANIFEST}  ({len(existing)} dong)")

    blanks = [r for r in existing.values() if float(r["ink_ratio"]) < 0.005]
    if blanks:
        print(f"CANH BAO: {len(blanks)} anh gan nhu trang, kiem tra lai:")
        for r in blanks[:10]:
            print(f"  - {r['image']} (ink={r['ink_ratio']})")


if __name__ == "__main__":
    main()
