"""Draw the test-retest sample from run 1, by the rule fixed in PROTOCOL.md.

30 research papers, 6 per concept level (run-1 classification), uniform within
level, seed 20261004. A level with fewer than 6 papers contributes all of them
and the shortfall is filled from the adjacent level with more papers.

    python reliability/draw_sample.py --run journal-analysis/ROMJIST_2026-10-04
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ruin_scoring as rs  # noqa: E402

SEED = 20261004
PER_LEVEL = 6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("reliability/sample.csv"))
    args = ap.parse_args()

    by_level: dict[int, list[dict]] = {lv: [] for lv in range(1, 6)}
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            if rs.is_research(p.get("flags") or []):
                by_level[int(p["concept_level"])].append({
                    "batch_id": batch["batch_id"],
                    "paper_id": p["paper_id"],
                    "source_file": p["paper"]["source_file"],
                    "concept_level": int(p["concept_level"]),
                    "final_run1": p["scores"]["final"],
                })
    for lv in by_level:   # deterministic order before sampling
        by_level[lv].sort(key=lambda r: (r["batch_id"], r["source_file"]))

    rng = random.Random(SEED)
    quota = {lv: PER_LEVEL for lv in by_level}
    for lv in sorted(by_level):
        short = quota[lv] - len(by_level[lv])
        if short > 0:
            quota[lv] = len(by_level[lv])
            neighbours = [n for n in (lv - 1, lv + 1) if n in by_level]
            donor = max(neighbours, key=lambda n: len(by_level[n]))
            quota[donor] += short
    sample = []
    for lv in sorted(by_level):
        sample += rng.sample(by_level[lv], quota[lv])

    with args.output.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sample[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sample)
    print(f"{len(sample)} papers -> {args.output}; quota {quota}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
