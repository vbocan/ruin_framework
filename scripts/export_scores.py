"""Export the per-paper RUIN score table as a single flat CSV.

The batch JSONs are the archive of record; this script flattens them into the
one-row-per-paper table used for downstream analysis (for example joining
citation counts onto the corpus) and published as the paper-level dataset
accompanying the manuscript.

Usage
-----
    python scripts/export_scores.py --output ruin_scores.csv

By default only research papers are exported. Pass ``--include-non-research``
to emit editorials and unreadable records too; their score columns are blank,
never zero, so that a downstream mean cannot silently absorb them.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402


COLUMNS = [
    "paper_id", "year", "volume", "issue", "batch_id",
    "title", "first_author", "n_authors", "pages", "doi",
    "record_type",
    "formalism", "citation_integrity", "structural_integrity",
    "artifact_availability", "intellectual_integrity", "composite", "final",
    "classification", "disqualified", "flags",
]


def rows(input_dir: Path, include_non_research: bool):
    for path in sorted(input_dir.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            batch = json.load(fh)
        src = batch["source"]
        for p in batch.get("papers", []):
            flags = p.get("flags", []) or []
            rtype = rs.record_type(flags)
            if rtype != rs.RECORD_RESEARCH and not include_non_research:
                continue
            meta = p.get("paper", {}) or {}
            authors = meta.get("authors") or []
            scores = p.get("scores", {}) or {}
            verdict = p.get("verdict", {}) or {}
            yield {
                "paper_id": p.get("paper_id", ""),
                "year": src.get("year", ""),
                "volume": src.get("volume", ""),
                "issue": src.get("issue", ""),
                "batch_id": batch.get("batch_id", ""),
                "title": meta.get("title", ""),
                "first_author": authors[0] if authors else "",
                "n_authors": len(authors),
                "pages": meta.get("pages") or "",
                "doi": meta.get("doi") or "",
                "record_type": rtype,
                **{
                    f: ("" if scores.get(f) is None else scores.get(f))
                    for f in (
                        "formalism", "citation_integrity", "structural_integrity",
                        "artifact_availability", "intellectual_integrity",
                        "composite", "final",
                    )
                },
                "classification": verdict.get("classification", ""),
                "disqualified": verdict.get("disqualified", ""),
                "flags": "|".join(flags),
            }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--input", type=Path,
        default=Path("journal-analysis/ROMJIST_29.12.2025"),
        help="Directory containing per-batch JSON files.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("ruin_scores.csv"),
        help="CSV file to write.",
    )
    parser.add_argument(
        "--include-non-research", action="store_true",
        help="Also emit editorials and unreadable records (blank scores).",
    )
    args = parser.parse_args()

    data = list(rows(args.input, args.include_non_research))
    if not data:
        raise SystemExit(f"No records found under {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)

    kinds = {}
    for r in data:
        kinds[r["record_type"]] = kinds.get(r["record_type"], 0) + 1
    print(f"Wrote {len(data)} rows to {args.output}")
    for kind, count in sorted(kinds.items()):
        print(f"    {kind:<12} {count}")


if __name__ == "__main__":
    main()
