"""Fix the run-5 sample: the papers on which the specification 1.2.1 rule is tested.

Every research paper that run 1 flagged FORMALISM_THEATER (72), and the 40
uncapped Level 1-2 controls of run 4 (reliability/capped/sample.csv). Run 4
analysed the same papers under specification 1.2.0, so comparing run 5 with
run 4 separates the effect of the stated rule from run-to-run variation.

    python reliability/spec121/draw_sample.py --run journal-analysis/ROMJIST_2026-10-04
"""

import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=HERE / "sample.csv")
    args = ap.parse_args()

    rows = []
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            if "FORMALISM_THEATER" in (p.get("flags") or []):
                rows.append({"batch_id": batch["batch_id"], "source_file": p["paper"]["source_file"],
                             "paper_id": p["paper_id"], "concept_level": int(p["concept_level"]),
                             "stratum": "theater"})
    capped = list(csv.DictReader((HERE.parent / "capped" / "sample.csv").open(encoding="utf-8")))
    for r in capped:
        if r["stratum"] == "control":
            rows.append({"batch_id": r["batch_id"], "source_file": r["source_file"], "paper_id": r["paper_id"],
                         "concept_level": int(r["concept_level"]), "stratum": "control"})
    rows.sort(key=lambda r: (r["batch_id"], r["source_file"]))
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{sum(r['stratum'] == 'theater' for r in rows)} theater + "
          f"{sum(r['stratum'] == 'control' for r in rows)} controls in "
          f"{len({r['batch_id'] for r in rows})} issues -> {args.output}")


if __name__ == "__main__":
    main()
