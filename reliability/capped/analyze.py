"""Capped-paper retest metrics, as fixed in PROTOCOL.md before run 4 was made.

Run 1 is the corpus run; run 4 re-analyses the sample in sample.csv once more.
Papers are matched by (batch_id, source_file), never by paper_id. Derived fields
are recomputed from the judged ones with scripts/ruin_scoring.py, so nothing
here trusts a derived value an agent may have written.

    python reliability/capped/analyze.py --run1 journal-analysis/ROMJIST_2026-10-04

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))

import ruin_scoring as rs  # noqa: E402

COMPONENTS = ("formalism", "citation_integrity", "structural_integrity", "artifact_availability")
CITATION_FLAGS = rs.DISQUALIFYING_FLAGS - rs.FORMALISM_FLAGS


def load(run_dir: Path) -> dict[tuple[str, str], dict]:
    out = {}
    for path in sorted(run_dir.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            out[(batch["batch_id"], p["paper"]["source_file"])] = p
    return out


def derived(p: dict) -> dict:
    """Final score, band and disqualifying flags, recomputed from judged fields."""
    flags = p.get("flags") or []
    level = int(p["concept_level"])
    d = rs.derive({c: p["scores"][c] for c in COMPONENTS}, flags, level)
    dq = rs.disqualifying(flags, level)
    return {"final": d["final"], "band": d["classification"], "dq": dq,
            "form": bool(dq & rs.FORMALISM_FLAGS), "cit": bool(dq & CITATION_FLAGS),
            "flags": set(flags), "level": level}


def share(num: int, den: int) -> dict:
    return {"n": num, "of": den, "share": round(num / den, 3) if den else None}


def kappa(a: float, b: float, c: float, d: float) -> float:
    """Cohen's kappa from a (possibly weighted) 2x2 table [[a, b], [c, d]]."""
    n = a + b + c + d
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", type=Path, required=True)
    ap.add_argument("--run4", type=Path, default=HERE.parent / "runs" / "run4")
    args = ap.parse_args()

    sample = list(csv.DictReader((HERE / "sample.csv").open(encoding="utf-8")))
    run1, run4 = load(args.run1), load(args.run4)
    keys = [(r["batch_id"], r["source_file"]) for r in sample]
    missing = [k for k in keys if k not in run4]
    if missing:
        sys.exit(f"{len(missing)} sampled papers missing from run 4, e.g. {missing[:3]}")
    nonres = [k for k in keys if not rs.is_research(run4[k].get("flags") or [])]

    rows = []
    for r, k in zip(sample, keys):
        if k in nonres:
            continue
        rows.append({"stratum": r["stratum"], "key": k,
                     "r1": derived(run1[k]), "r4": derived(run4[k])})
    capped = [x for x in rows if x["stratum"] != "control"]
    controls = [x for x in rows if x["stratum"] == "control"]

    res: dict = {"n_sampled": len(sample), "typed_non_research_in_run4": [list(k) for k in nonres],
                 "n_capped": len(capped), "n_controls": len(controls)}

    # 1. Does the cap reproduce?
    res["cap_reproduced"] = {"all_capped": share(sum(bool(x["r4"]["dq"]) for x in capped), len(capped))}
    for s in ("capped_formalism", "capped_citation", "capped_both"):
        grp = [x for x in capped if x["stratum"] == s]
        res["cap_reproduced"][s] = share(sum(bool(x["r4"]["dq"]) for x in grp), len(grp))
    form1 = [x for x in capped if x["r1"]["form"]]
    cit1 = [x for x in capped if x["r1"]["cit"]]
    res["family_reproduced"] = {
        "formalism_cap_by_formalism_flag": share(sum(x["r4"]["form"] for x in form1), len(form1)),
        "citation_cap_by_citation_flag": share(sum(x["r4"]["cit"] for x in cit1), len(cit1)),
    }

    # 2. Per-flag persistence among sampled papers that carried the flag in run 1.
    res["flag_persistence"] = {}
    for f in sorted(rs.DISQUALIFYING_FLAGS):
        had = [x for x in rows if f in x["r1"]["flags"]]
        if had:
            res["flag_persistence"][f] = share(sum(f in x["r4"]["flags"] for x in had), len(had))

    # 3. The concept level that gates the formalism cap.
    res["formalism_capped_level"] = {
        "level_identical": share(sum(x["r4"]["level"] == x["r1"]["level"] for x in form1), len(form1)),
        "still_level_1_or_2": share(sum(x["r4"]["level"] in (1, 2) for x in form1), len(form1)),
    }

    # 4. New caps among controls.
    res["controls_newly_capped"] = {
        "any": share(sum(bool(x["r4"]["dq"]) for x in controls), len(controls)),
        "formalism": share(sum(x["r4"]["form"] for x in controls), len(controls)),
        "citation": share(sum(x["r4"]["cit"] for x in controls), len(controls)),
    }

    # 5. Bands and final scores.
    def band_same(grp):
        return share(sum(x["r1"]["band"] == x["r4"]["band"] for x in grp), len(grp))
    res["band_identical"] = {"capped": band_same(capped), "controls": band_same(controls)}
    lost = [x for x in capped if not x["r4"]["dq"]]
    res["capped_papers_losing_cap"] = {
        "n": len(lost),
        "run4_bands": {b: sum(x["r4"]["band"] == b for x in lost)
                       for b in ("CRITICAL", "CONCERNING", "LIMITED", "ADEQUATE", "STRONG")},
        "run4_final_median": round(st.median([x["r4"]["final"] for x in lost]), 1) if lost else None,
    }
    diffs = [abs(x["r1"]["final"] - x["r4"]["final"]) for x in controls]
    res["controls_final_abs_diff"] = {"mean": round(st.mean(diffs), 2), "median": round(st.median(diffs), 2)}

    # 6. Agreement on the disqualification decision among Level 1-2 papers,
    #    weighting controls by the inverse of their sampling fraction.
    pool_size = sum(1 for p in run1.values()
                    if rs.is_research(p.get("flags") or []) and int(p["concept_level"]) in (1, 2)
                    and not rs.disqualifying(p.get("flags") or [], int(p["concept_level"])))
    w_ctrl = pool_size / len(controls)
    l12_capped = [x for x in capped if x["r1"]["level"] in (1, 2)]
    a = sum(bool(x["r4"]["dq"]) for x in l12_capped)            # capped, capped
    b = len(l12_capped) - a                                      # capped, not
    c = w_ctrl * sum(bool(x["r4"]["dq"]) for x in controls)      # not, capped
    d = w_ctrl * sum(not x["r4"]["dq"] for x in controls)        # not, not
    res["level12_disqualification_weighted"] = {
        "uncapped_pool": pool_size, "control_weight": round(w_ctrl, 3),
        "observed_agreement": round((a + d) / (a + b + c + d), 3),
        "positive_agreement": round(2 * a / (2 * a + b + c), 3),
        "cohen_kappa": round(kappa(a, b, c, d), 3),
    }

    out = HERE / "results.json"
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
