"""Merge two independent artifact-classification passes into the final re-assessment.

The artifact re-assessment was judged twice, independently, from the same
evidence file (journal-analysis/ROMJIST_29.12.2025/artifact_reassessment/artifact_evidence.jsonl) and the same rubric
(framework/scoring.md, Artifact Availability Score). This script

    1. reports agreement between the passes: raw agreement, Cohen's kappa on the
       five categories, and agreement on the score itself;
    2. takes the category both passes agree on, and for every disagreement the
       ruling recorded in journal-analysis/ROMJIST_29.12.2025/artifact_reassessment/artifact_adjudication.csv, which must cover every
       disagreement and nothing else;
    3. writes journal-analysis/ROMJIST_29.12.2025/artifact_reassessment/artifact_rescore.csv, the input to apply_artifact_rescore.py.

Usage
-----
    python scripts/artifact_agreement.py            # report + write
    python scripts/artifact_agreement.py --report   # report only, list disagreements
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "journal-analysis" / "ROMJIST_29.12.2025" / "artifact_reassessment"
CATS = list(rs.ARTIFACT_ANCHORS)


def load(path: Path) -> dict[str, dict]:
    rows = {r["paper_id"]: r for r in csv.DictReader(path.open(encoding="utf-8"))}
    for pid, r in rows.items():
        if r["category"] not in rs.ARTIFACT_ANCHORS:
            sys.exit(f"{path.name}: {pid} has unknown category {r['category']!r}")
    return rows


def kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in CATS) / (n * n)
    return (po - pe) / (1 - pe)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--assessor", default="claude-opus-5-5")
    ap.add_argument("--assessed", default="2026-10-04")
    args = ap.parse_args()

    a, b = load(DATA / "artifact_pass_a.csv"), load(DATA / "artifact_pass_b.csv")
    if set(a) != set(b):
        sys.exit(f"passes cover different papers: {sorted(set(a) ^ set(b))[:5]}")
    ids = list(a)
    pairs = [(a[i]["category"], b[i]["category"]) for i in ids]
    agree = sum(x == y for x, y in pairs)
    mad = sum(abs(rs.artifact_score(x) - rs.artifact_score(y)) for x, y in pairs) / len(pairs)
    rel = sum(a[i]["relevant"].lower() == b[i]["relevant"].lower() for i in ids)

    print(f"papers: {len(ids)}")
    print(f"category agreement: {agree}/{len(ids)} = {100 * agree / len(ids):.1f}%")
    print(f"Cohen's kappa (5 categories): {kappa(pairs):.3f}")
    print(f"mean absolute score difference: {mad:.2f} points")
    print(f"'relevant' agreement: {rel}/{len(ids)}")
    print("pass A:", dict(Counter(x for x, _ in pairs)))
    print("pass B:", dict(Counter(y for _, y in pairs)))
    print("confusion (A -> B, disagreements only):",
          dict(Counter(f"{x}->{y}" for x, y in pairs if x != y)))

    disagreements = [i for i in ids if a[i]["category"] != b[i]["category"]]
    if args.report:
        for i in disagreements:
            print(f"\n{i}: A={a[i]['category']} | {a[i]['evidence']} | {a[i]['note']}")
            print(f"{' ' * len(i)}  B={b[i]['category']} | {b[i]['evidence']} | {b[i]['note']}")
        return 0

    adj_path = DATA / "artifact_adjudication.csv"
    adj = {r["paper_id"]: r for r in csv.DictReader(adj_path.open(encoding="utf-8"))}
    # Besides the disagreements, the adjudication may mark a paper unassessed: one
    # whose source text could not be obtained, which both passes necessarily
    # scored from no evidence at all.
    missing = set(disagreements) - set(adj)
    extra = {i for i in set(adj) - set(disagreements)
             if adj[i]["category"] != rs.ARTIFACT_UNASSESSED}
    if missing or extra:
        sys.exit(f"adjudication must cover exactly the disagreements; "
                 f"missing {sorted(missing)[:5]}, extra {sorted(extra)[:5]}")

    out = DATA / "artifact_rescore.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["paper_id", "category", "relevant", "evidence", "basis", "assessor", "assessed"])
        for i in ids:
            if i in adj:
                r = adj[i]
                cat, relevant, ev, basis = r["category"], r["relevant"], r["evidence"], "adjudicated"
            else:
                cat = a[i]["category"]
                relevant = a[i]["relevant"] if a[i]["relevant"].lower() == b[i]["relevant"].lower() \
                    else "true"
                ev, basis = a[i]["evidence"], "both passes"
            if cat not in rs.ARTIFACT_ANCHORS and cat != rs.ARTIFACT_UNASSESSED:
                sys.exit(f"{i}: unknown category {cat!r}")
            w.writerow([i, cat, relevant.lower(), ev, basis, args.assessor, args.assessed])
    final = Counter(r["category"] for r in csv.DictReader(out.open(encoding="utf-8")))
    print(f"\nwrote {out.name}: {dict(final)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
