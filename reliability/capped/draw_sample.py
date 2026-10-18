"""Draw the capped-paper retest sample from run 1, by the rule fixed in PROTOCOL.md.

Every research paper that run 1 disqualified (capped at 24), plus 40 controls
drawn uniformly, seed 20261018, from the research papers at concept Levels 1-2
that run 1 did not disqualify.

    python reliability/capped/draw_sample.py --run journal-analysis/ROMJIST_2026-10-04
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import ruin_scoring as rs  # noqa: E402

SEED = 20261018
N_CONTROLS = 40
HERE = Path(__file__).resolve().parent


def stratum(flags: list[str], level: int) -> str:
    dq = rs.disqualifying(flags, level)
    if not dq:
        return "control"
    form, cit = bool(dq & rs.FORMALISM_FLAGS), bool(dq - rs.FORMALISM_FLAGS)
    return "capped_both" if form and cit else "capped_formalism" if form else "capped_citation"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=HERE / "sample.csv")
    args = ap.parse_args()

    capped, pool = [], []
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            flags = p.get("flags") or []
            if not rs.is_research(flags):
                continue
            level = int(p["concept_level"])
            row = {
                "batch_id": batch["batch_id"],
                "source_file": p["paper"]["source_file"],
                "paper_id": p["paper_id"],
                "concept_level": level,
                "stratum": stratum(flags, level),
                "final_run1": p["scores"]["final"],
                "flags_run1": "|".join(sorted(flags)),
            }
            if row["stratum"] != "control":
                capped.append(row)
            elif level in (1, 2):
                pool.append(row)

    key = lambda r: (r["batch_id"], r["source_file"])  # noqa: E731
    capped.sort(key=key)
    pool.sort(key=key)   # deterministic order before sampling
    controls = sorted(random.Random(SEED).sample(pool, N_CONTROLS), key=key)
    sample = sorted(capped + controls, key=key)

    with args.output.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sample[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sample)
    batches = sorted({r["batch_id"] for r in sample})
    print(f"{len(capped)} capped + {len(controls)} controls (from {len(pool)} uncapped "
          f"Level 1-2 papers) = {len(sample)} papers in {len(batches)} issues -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
