"""Write the artifact re-assessment into the batch JSONs.

data/artifact_rescore.csv holds one judged row per research paper: the
artifact category, whether the paper has anything to release, and the verbatim
evidence the category rests on. This script copies each row into its paper's
``artifact_assessment`` block, sets ``scores.artifact_availability`` to the
category's anchor through :func:`ruin_scoring.artifact_score`, keeps the score
it replaces as ``original_score``, and records the model identifiers on every
batch. It never touches a derived field; run ``rescore.py --write`` afterwards.

Idempotent: a paper whose block already matches its CSV row is left alone, and
``original_score`` is written once and never overwritten.

Usage
-----
    python scripts/apply_artifact_rescore.py \\
        --input journal-analysis/ROMJIST_29.12.2025 \\
        --rescore data/artifact_rescore.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402

#: Model that produced the judged fields of the ROMJIST_29.12.2025 run, as
#: recorded by the authors. The run outputs did not log it at the time.
ANALYSIS_MODEL = "claude-opus-4-5"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", type=Path, default=Path("journal-analysis/ROMJIST_29.12.2025"))
    ap.add_argument("--rescore", type=Path, default=Path("data/artifact_rescore.csv"))
    args = ap.parse_args()

    rows = {r["paper_id"]: r for r in csv.DictReader(args.rescore.open(encoding="utf-8"))}
    seen: set[str] = set()
    changed = 0

    for path in sorted(args.input.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        before = json.dumps(batch, sort_keys=True)
        models = {"analysis": ANALYSIS_MODEL}
        for p in batch.get("papers", []):
            if not rs.is_research(p.get("flags", []) or []):
                continue
            pid = p["paper_id"]
            row = rows.get(pid)
            if row is None:
                sys.exit(f"{path.name}: research paper {pid} has no row in {args.rescore}")
            seen.add(pid)
            prior = p.get("artifact_assessment") or {}
            original = prior.get("original_score", p["scores"].get("artifact_availability"))
            p["artifact_assessment"] = {
                "category": row["category"],
                "relevant": row["relevant"].strip().lower() == "true",
                "evidence": row["evidence"],
                "assessor": row["assessor"],
                "assessed": row["assessed"],
                "original_score": original,
            }
            if row["category"] != rs.ARTIFACT_UNASSESSED:
                p["scores"]["artifact_availability"] = rs.artifact_score(row["category"])
            models["artifact_reassessment"] = row["assessor"]
        batch["models"] = models
        if json.dumps(batch, sort_keys=True) != before:
            changed += 1
            with path.open("w", encoding="utf-8", newline="\n") as fh:
                json.dump(batch, fh, indent=1, ensure_ascii=False)
                fh.write("\n")

    extra = set(rows) - seen
    if extra:
        sys.exit(f"{len(extra)} CSV rows match no research paper: {sorted(extra)[:5]}")
    print(f"{len(seen)} papers re-assessed; {changed} batch files rewritten.")
    print("Now run: python scripts/rescore.py --write && python scripts/rescore.py --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
