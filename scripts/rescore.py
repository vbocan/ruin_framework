"""Audit and repair derived score fields in the published batch JSONs.

Every batch file records both the assessor's judgments (component scores,
flags, provenance) and quantities derived from them (intellectual integrity,
composite, final score, disqualification, classification). Only the judgments
are authoritative. This tool re-derives the rest through
:mod:`ruin_scoring` so that the archived corpus and the published
specification agree exactly.

Usage
-----
Report discrepancies without modifying anything::

    python scripts/rescore.py --check

Rewrite the batch files so their derived fields are canonical::

    python scripts/rescore.py --write

``--check`` exits non-zero when any discrepancy remains, which makes it usable
as a continuous-integration guard against the archived data drifting from the
specification again.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402


TOLERANCE = 0.01


def audit_paper(paper: dict) -> tuple[dict, list[str]]:
    """Return canonical fields for a paper and the discrepancies found.

    For a non-research record the canonical scores are ``None``: an editorial
    is not research, and an unreadable PDF was never assessed. Scoring either
    as zero would silently depress every statistic it enters.
    """
    flags = paper.get("flags", []) or []
    rtype = rs.record_type(flags)
    scores = paper.get("scores") or {}
    verdict = paper.get("verdict") or {}
    issues: list[str] = []

    if rtype != rs.RECORD_RESEARCH:
        canonical = {
            "scores": {f: None for f in rs.COMPONENT_FIELDS + rs.DERIVED_FIELDS},
            "verdict": {
                "classification": "NOT_APPLICABLE",
                "disqualified": False,
                "record_type": rtype,
            },
        }
        if any(scores.get(f) is not None for f in rs.DERIVED_FIELDS):
            issues.append(
                f"non-research record ({rtype}) carried a score "
                f"(final={scores.get('final')}); cleared to null"
            )
        if verdict.get("classification") != "NOT_APPLICABLE":
            issues.append(
                f"non-research record classified "
                f"{verdict.get('classification')!r}; set to NOT_APPLICABLE"
            )
        return canonical, issues

    derived = rs.derive(scores, flags)

    for field in rs.DERIVED_FIELDS:
        stated = scores.get(field)
        if stated is None:
            issues.append(f"{field} absent; derived {derived[field]}")
        elif abs(float(stated) - derived[field]) > TOLERANCE:
            issues.append(f"{field}: stated {stated}, derived {derived[field]}")

    if verdict.get("classification") != derived["classification"]:
        issues.append(
            f"classification: stated {verdict.get('classification')!r}, "
            f"derived {derived['classification']!r}"
        )
    if bool(verdict.get("disqualified")) != derived["disqualified"]:
        issues.append(
            f"disqualified: stated {verdict.get('disqualified')!r}, "
            f"derived {derived['disqualified']!r}"
        )

    canonical = {
        "scores": {
            **{f: scores[f] for f in rs.COMPONENT_FIELDS},
            "intellectual_integrity": derived["intellectual_integrity"],
            "composite": derived["composite"],
            "final": derived["final"],
        },
        "verdict": {
            **verdict,
            "classification": derived["classification"],
            "disqualified": derived["disqualified"],
            "record_type": rs.RECORD_RESEARCH,
        },
    }
    return canonical, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("journal-analysis/ROMJIST_29.12.2025"),
        help="Directory containing per-batch JSON files.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report discrepancies only.")
    mode.add_argument("--write", action="store_true", help="Rewrite derived fields.")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress the per-paper listing."
    )
    args = parser.parse_args()

    files = sorted(args.input.glob("*.json"))
    if not files:
        raise SystemExit(f"No batch JSONs found under {args.input}")

    total_papers = 0
    changed_papers = 0
    all_issues: list[str] = []
    kinds: Counter[str] = Counter()

    for path in files:
        with path.open(encoding="utf-8") as fh:
            batch = json.load(fh)

        batch_changed = False
        for paper in batch.get("papers", []):
            total_papers += 1
            canonical, issues = audit_paper(paper)
            if issues:
                changed_papers += 1
                pid = paper.get("paper_id", "?")
                for issue in issues:
                    all_issues.append(f"{path.name} :: {pid} :: {issue}")
                    kinds[issue.split(":")[0]] += 1
            if canonical["scores"] != paper.get("scores") or canonical[
                "verdict"
            ] != paper.get("verdict"):
                paper["scores"] = canonical["scores"]
                paper["verdict"] = canonical["verdict"]
                batch_changed = True

        if args.write and batch_changed:
            with path.open("w", encoding="utf-8", newline="\n") as fh:
                json.dump(batch, fh, indent=1, ensure_ascii=False)
                fh.write("\n")

    if not args.quiet:
        for issue in all_issues:
            print(issue)
        if all_issues:
            print()

    print(f"Batches:            {len(files)}")
    print(f"Paper records:      {total_papers}")
    print(f"Records corrected:  {changed_papers}")
    print(f"Discrepancies:      {len(all_issues)}")
    for kind, count in kinds.most_common():
        print(f"    {kind:<32} {count}")

    if args.write:
        print("\nDerived fields rewritten. Re-run with --check to confirm.")
        return 0

    if all_issues:
        print("\nFAIL: archived data does not match the specification.")
        return 1
    print("\nOK: archived data matches the specification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
