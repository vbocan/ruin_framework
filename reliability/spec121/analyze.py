"""Run-5 metrics: does the stated Necessity Test rule change the formalism flags?

Written before run 5, as fixed in PROTOCOL.md. Papers are matched by
(batch_id, source_file). Run 1 is the corpus run and run 4 the retest, both
under specification 1.2.0; run 5 analyses the same 112 papers under 1.2.1.

    python reliability/spec121/analyze.py --run1 journal-analysis/ROMJIST_2026-10-04

Standard library only.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))

import ruin_scoring as rs  # noqa: E402

ELEMENT = re.compile(r"Q1\s*[:=]?\s*(yes|no)\W+Q2\s*[:=]?\s*(yes|no)\W+Q3\s*[:=]?\s*(yes|no)", re.I)


def load(run_dir):
    out = {}
    for path in sorted(Path(run_dir).glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            out[(batch["batch_id"], p["paper"]["source_file"])] = p
    return out


def share(n, d):
    return {"n": n, "of": d, "share": round(n / d, 3) if d else None}


def necessity_section(provenance):
    """Per-element answers recorded under the provenance's Necessity Test heading."""
    m = re.search(r"#+\s*Necessity Test\s*\n(.*?)(?=\n#+\s|\Z)", provenance or "", re.S | re.I)
    if not m:
        return None
    return [tuple(a.lower() for a in e.groups()) for e in ELEMENT.finditer(m.group(1))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", type=Path, required=True)
    ap.add_argument("--run4", type=Path, default=HERE.parent / "runs" / "run4")
    ap.add_argument("--run5", type=Path, default=HERE.parent / "runs" / "run5")
    args = ap.parse_args()

    sample = list(csv.DictReader((HERE / "sample.csv").open(encoding="utf-8")))
    r1, r4, r5 = load(args.run1), load(args.run4), load(args.run5)
    keys = [(s["batch_id"], s["source_file"]) for s in sample]
    missing = [k for k in keys if k not in r5]
    if missing:
        sys.exit(f"{len(missing)} sampled papers missing from run 5, e.g. {missing[:3]}")
    ft = lambda p: "FORMALISM_THEATER" in (p.get("flags") or [])  # noqa: E731
    theater = [k for s, k in zip(sample, keys) if s["stratum"] == "theater"]
    controls = [k for s, k in zip(sample, keys) if s["stratum"] == "control"]

    res = {"n_theater": len(theater), "n_controls": len(controls)}
    res["theater_flag_recurs"] = {"run4_spec120": share(sum(ft(r4[k]) for k in theater), len(theater)),
                                  "run5_spec121": share(sum(ft(r5[k]) for k in theater), len(theater))}
    res["controls_gain_flag"] = {"run4_spec120": share(sum(ft(r4[k]) for k in controls), len(controls)),
                                 "run5_spec121": share(sum(ft(r5[k]) for k in controls), len(controls))}
    both = theater + controls
    res["run4_vs_run5_discordant"] = {
        "flag_in_run4_only": sum(ft(r4[k]) and not ft(r5[k]) for k in both),
        "flag_in_run5_only": sum(ft(r5[k]) and not ft(r4[k]) for k in both),
    }
    res["level_same_as_run1"] = {"run4": share(sum(r4[k]["concept_level"] == r1[k]["concept_level"] for k in both), len(both)),
                                 "run5": share(sum(r5[k]["concept_level"] == r1[k]["concept_level"] for k in both), len(both))}

    # per-element answers recorded under specification 1.2.1
    recorded = consistent = elements = unnecessary = 0
    for k in both:
        p = r5[k]
        answers = necessity_section(p.get("provenance"))
        if answers is None:
            continue
        recorded += 1
        elements += len(answers)
        n_unnec = sum(a == ("yes", "no", "no") for a in answers)
        unnecessary += n_unnec
        eligible = int(p["concept_level"]) in (1, 2)
        expected = eligible and n_unnec > 0
        consistent += expected == ft(p)
    res["per_question_records"] = {
        "papers_with_section": share(recorded, len(both)),
        "elements_recorded": elements,
        "elements_unnecessary": unnecessary,
        "flag_consistent_with_recorded_answers": share(consistent, recorded),
    }

    def disq(p):
        return bool(rs.disqualifying(p.get("flags") or [], int(p["concept_level"])))
    res["disqualified"] = {"run1": sum(disq(r1[k]) for k in both), "run4": sum(disq(r4[k]) for k in both),
                           "run5": sum(disq(r5[k]) for k in both)}
    out = HERE / "results.json"
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
