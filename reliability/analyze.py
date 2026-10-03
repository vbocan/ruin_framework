"""Test-retest metrics for the 30-paper sample, as fixed in PROTOCOL.md.

Run 1 is the corpus run; runs 2 and 3 are the independent repeats. Papers are
matched across runs by (batch_id, source_file), never by paper_id, which each
run assigns for itself.

    python reliability/analyze.py --run1 journal-analysis/ROMJIST_2026-10-04
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ruin_scoring as rs  # noqa: E402

HERE = Path(__file__).resolve().parent
SCORES = ["formalism", "citation_integrity", "structural_integrity",
          "artifact_availability", "intellectual_integrity", "composite", "final"]
BOUNDARIES = (25.0, 40.0, 60.0, 80.0)


def load(run_dir: Path) -> dict[tuple[str, str], dict]:
    out = {}
    for path in sorted(run_dir.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            out[(batch["batch_id"], p["paper"]["source_file"])] = p
    return out


def mad(x: np.ndarray) -> tuple[float, float]:
    """Mean absolute pairwise difference per paper; mean and SD across papers."""
    per = np.array([np.mean([abs(a - b) for a, b in itertools.combinations(row, 2)]) for row in x])
    return float(per.mean()), float(per.std(ddof=1))


def icc21(x: np.ndarray) -> float:
    """ICC(2,1): two-way random effects, absolute agreement, single rater."""
    n, k = x.shape
    grand = x.mean()
    msr = k * ((x.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msc = n * ((x.mean(axis=0) - grand) ** 2).sum() / (k - 1)
    sse = ((x - x.mean(axis=1, keepdims=True) - x.mean(axis=0, keepdims=True) + grand) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    denom = msr + (k - 1) * mse + k * (msc - mse) / n
    return float((msr - mse) / denom) if denom else float("nan")


def fleiss(labels: list[list[str]]) -> float:
    cats = sorted({c for row in labels for c in row})
    n, k = len(labels), len(labels[0])
    counts = np.array([[row.count(c) for c in cats] for row in labels], float)
    p_i = ((counts ** 2).sum(axis=1) - k) / (k * (k - 1))
    p_j = counts.sum(axis=0) / (n * k)
    pe = (p_j ** 2).sum()
    return float((p_i.mean() - pe) / (1 - pe)) if pe < 1 else 1.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", type=Path, required=True)
    args = ap.parse_args()

    sample = list(csv.DictReader((HERE / "sample.csv").open(encoding="utf-8")))
    runs = [load(args.run1), load(HERE / "runs" / "run2"), load(HERE / "runs" / "run3")]
    keys = [(r["batch_id"], r["source_file"]) for r in sample]
    missing = [(i + 1, k) for i, run in enumerate(runs) for k in keys if k not in run]
    if missing:
        sys.exit(f"missing records: {missing[:5]}")
    recs = [[run[k] for run in runs] for k in keys]
    nonres = [k for k, row in zip(keys, recs) if not all(rs.is_research(p.get("flags") or []) for p in row)]

    res: dict = {"n_papers": len(keys), "n_runs": 3,
                 "papers_typed_non_research_in_some_run": [list(k) for k in nonres]}
    use = [row for k, row in zip(keys, recs) if k not in nonres]

    res["scores"] = {}
    for f in SCORES:
        x = np.array([[float(p["scores"][f]) for p in row] for row in use])
        m, s = mad(x)
        res["scores"][f] = {"mad": round(m, 2), "mad_sd": round(s, 2), "icc21": round(icc21(x), 3)}

    def cat(field):
        lab = [[str(field(p)) for p in row] for row in use]
        return {"fleiss_kappa": round(fleiss(lab), 3),
                "all_three_agree": sum(len(set(r)) == 1 for r in lab)}

    res["classification"] = cat(lambda p: p["verdict"]["classification"])
    res["concept_level"] = cat(lambda p: p["concept_level"])
    res["artifact_category"] = cat(lambda p: (p.get("artifact_assessment") or {}).get("category"))
    res["near_boundary_run1"] = sum(
        any(abs(float(row[0]["scores"]["final"]) - b) < 3 for b in BOUNDARIES) for row in use)

    flags = sorted({f for row in use for p in row for f in (p.get("flags") or [])})
    res["flags"] = {}
    for f in flags:
        pres = [[f in (p.get("flags") or []) for p in row] for row in use]
        res["flags"][f] = {"papers_flagged_in_any_run": sum(any(r) for r in pres),
                           "all_three_agree_share": round(sum(len(set(r)) == 1 for r in pres) / len(pres), 3)}

    out = HERE / "results.json"
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
