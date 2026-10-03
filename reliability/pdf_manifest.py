"""Write the SHA-256 manifest of the corpus PDFs analysed in the re-run.

The PDFs are the journal's content and are not redistributed. The manifest lets
anyone who re-downloads the corpus with tools/Download-ROMJIST.ps1 confirm they
hold byte-identical files.

    python reliability/pdf_manifest.py --corpus /path/to/ROMJIST_corpus
"""

import argparse
import csv
import hashlib
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("reliability/pdf_manifest.csv"))
    args = ap.parse_args()
    rows = []
    for pdf in sorted(args.corpus.glob("*/*.pdf")):
        rows.append({"batch_id": pdf.parent.name, "source_file": pdf.name,
                     "bytes": pdf.stat().st_size,
                     "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()})
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} PDFs -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
