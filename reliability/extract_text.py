"""Convert every corpus PDF to text once, so every run reads identical input.

The Read tool on the analysis machine cannot render PDFs (poppler's pdftoppm is
absent), so agents fell back to pdftotext with whatever options they chose. To
keep the input fixed across runs, every PDF is converted once, with one
command, and the text's SHA-256 is added to the manifest beside the PDF's:

    pdftotext -enc UTF-8 -layout <pdf> <txt>

The text files are derived from the journal's content and are not published;
re-run this script on a re-downloaded corpus and compare hashes.

    python reliability/extract_text.py --corpus /corpus --text /corpus_text
"""

import argparse
import csv
import hashlib
import subprocess
from pathlib import Path

MANIFEST = Path("reliability/pdf_manifest.csv")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--text", type=Path, required=True)
    args = ap.parse_args()
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    for r in rows:
        pdf = args.corpus / r["batch_id"] / r["source_file"]
        txt = args.text / r["batch_id"] / (r["source_file"][:-4] + ".txt")
        txt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), str(txt)], check=False)
        data = txt.read_bytes() if txt.exists() else b""
        r["text_chars"] = len(data.decode("utf-8", "replace"))
        r["text_sha256"] = hashlib.sha256(data).hexdigest()
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    empty = [r["source_file"] for r in rows if int(r["text_chars"]) < 500]
    print(f"{len(rows)} PDFs converted; {len(empty)} with under 500 characters: {empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
