"""How stable are RUIN's classifications, and how much do the scoring rules decide them?

Reproduces Section 4.6 and Table 5 of the manuscript from the published
judgments. Four questions:

  A. What the cap does: the formalism or citation finding lowers its component
     score and then caps the total, so it enters the score twice.
  B. Rule sensitivity: the band distribution under alternative scoring rules
     (no cap, other self-citation lines, other weights), each applied to the
     published judgments. No model is involved; only the arithmetic changes.
  C. Model sensitivity: band and disqualification agreement across the three
     test-retest runs, and the share of uncapped papers expected to change band
     on one re-run, from the retest's own run-to-run differences.
  D. Self-citation counts: the ratios the model recorded in its flag details,
     and how often the flag it raised matches the published thresholds.

Run 4, the retest of every capped paper, has its own analysis in
reliability/capped/analyze.py. Standard library only; scripts/aggregate.py
calls this module and writes Table 5 next to Tables 1-4.

    python scripts/classification_stability.py
"""

import argparse
import collections
import csv
import glob
import itertools
import json
import random
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BANDS = ("CRITICAL", "CONCERNING", "LIMITED", "ADEQUATE", "STRONG")
COMPONENTS = ("formalism", "citation_integrity", "structural_integrity", "artifact_availability")
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
SC_FLAGS = {"EXCESSIVE_SELF_CITATION", "ELEVATED_SELF_CITATION"}


def flags_of(r):
    return set(x for x in (r["flags"] or "").split("|") if x)


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    rk = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[order[k]] = (i + j) / 2
        i = j + 1
    return rk


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ma, mb = st.mean(ra), st.mean(rb)
    num = sum((p - ma) * (q - mb) for p, q in zip(ra, rb))
    return num / (sum((p - ma) ** 2 for p in ra) ** 0.5 * sum((q - mb) ** 2 for q in rb) ** 0.5)


def scr_from_details(text):
    """Self-citation ratio from the model's own words, e.g. '9 of 33 references'."""
    m = re.search(r"\b(?:All\s+)?(\d+|[A-Za-z]+)\s+(?:of|out of|/)\s+(\d+)\b", text)
    if m:
        a = m.group(1).lower()
        a = int(a) if a.isdigit() else WORDS.get(a)
        if a is not None and int(m.group(2)):
            return a / int(m.group(2))
    m = re.search(r"\bAll\s+(\d+)\s+references", text)
    return 1.0 if m else None


def compute(fw=REPO):
    sys.path.insert(0, str(Path(fw) / "scripts"))
    import ruin_scoring as rs

    rows = [r for r in csv.DictReader(open(Path(fw) / "data" / "ruin_scores.csv", encoding="utf-8"))
            if r["record_type"] == "research"]
    F = lambda r, k: float(r[k])  # noqa: E731
    lvl = lambda r: int(r["concept_level"])  # noqa: E731
    pub = [F(r, "final") for r in rows]
    band0 = [r["classification"] for r in rows]
    out = {"n": len(rows)}

    def group(r):
        dq = rs.disqualifying(flags_of(r), lvl(r))
        if not dq:
            return "uncapped"
        f, c = bool(dq & rs.FORMALISM_FLAGS), bool(dq - rs.FORMALISM_FLAGS)
        return "both" if f and c else "formalism" if f else "citation"

    # --- A. the double count
    g = collections.defaultdict(list)
    for r in rows:
        g[group(r)].append(r)
    form_capped = g["formalism"] + g["both"]
    out["A"] = {
        "formalism_capped": len(form_capped),
        "formalism_capped_with_formalism_zero": sum(F(r, "formalism") == 0 for r in form_capped),
        "uncapped_formalism_median": st.median(F(r, "formalism") for r in g["uncapped"]),
        "uncapped_citation_mean": round(st.mean(F(r, "citation_integrity") for r in g["uncapped"]), 1),
        "citation_only_capped_citation_mean": round(st.mean(F(r, "citation_integrity") for r in g["citation"]), 1),
        "citation_only_capped": len(g["citation"]),
        "citation_only_composite_mean": round(st.mean(F(r, "composite") for r in g["citation"]), 1),
        "citation_only_composite_bands": dict(collections.Counter(rs.classify(F(r, "composite")) for r in g["citation"])),
        "formalism_only_composite_bands": dict(collections.Counter(rs.classify(F(r, "composite")) for r in g["formalism"])),
    }
    # worked example: LifeTags with a proportionate formalism score
    w = next(r for r in rows if "LifeTags" in r["title"])
    comp = {k: F(w, k) for k in COMPONENTS}
    comp["formalism"] = out["A"]["uncapped_formalism_median"]
    cf = rs.derive(comp, flags_of(w) - rs.DISQUALIFYING_FLAGS, lvl(w))
    out["A"]["worked_example"] = {"published_composite": F(w, "composite"), "published_final": F(w, "final"),
                                  "counterfactual_composite": cf["composite"], "counterfactual_final": cf["final"],
                                  "counterfactual_band": cf["classification"]}

    # --- D. self-citation ratios recorded by the model
    scr = {}
    for path in glob.glob(str(Path(fw) / "journal-analysis" / "ROMJIST_2026-10-04" / "*.json")):
        batch = json.load(open(path, encoding="utf-8"))
        for p in batch["papers"]:
            fd = p.get("flag_details") or {}
            for k in ("EXCESSIVE_SELF_CITATION", "ELEVATED_SELF_CITATION"):
                if k in fd:
                    v = scr_from_details(fd[k])
                    if v is not None:
                        scr[(batch["batch_id"], p["paper"]["source_file"])] = (k, v)
    # ruin_scores.csv has no source_file column; match on paper_id through the batch files instead
    pid2key = {}
    for path in glob.glob(str(Path(fw) / "journal-analysis" / "ROMJIST_2026-10-04" / "*.json")):
        batch = json.load(open(path, encoding="utf-8"))
        for p in batch["papers"]:
            pid2key[(batch["batch_id"], p["paper_id"])] = (batch["batch_id"], p["paper"]["source_file"])
    SCR = {}
    for r in rows:
        k = pid2key.get((r["batch_id"], r["paper_id"]))
        if k in scr:
            SCR[r["paper_id"]] = scr[k][1]
    exc = [r for r in rows if "EXCESSIVE_SELF_CITATION" in flags_of(r)]
    ele = [r for r in rows if "ELEVATED_SELF_CITATION" in flags_of(r)]
    vals = sorted(SCR.values())
    mismatch = [r["paper_id"] for r in exc if r["paper_id"] in SCR and SCR[r["paper_id"]] <= 0.30] + \
               [r["paper_id"] for r in ele if r["paper_id"] in SCR and not 0.20 <= SCR[r["paper_id"]] <= 0.30]
    at20 = [r["paper_id"] for r in ele if r["paper_id"] in SCR and abs(SCR[r["paper_id"]] - 0.20) < 1e-9]
    out["D"] = {"excessive_with_ratio": sum(r["paper_id"] in SCR for r in exc), "excessive": len(exc),
                "elevated_with_ratio": sum(r["paper_id"] in SCR for r in ele), "elevated": len(ele),
                "median_ratio_flagged": round(st.median(vals), 3),
                "excessive_between_30_and_35": sum(0.30 < SCR.get(r["paper_id"], 0) <= 0.35 for r in exc),
                "flag_ratio_mismatch": mismatch, "elevated_at_exactly_20": at20}

    # --- B. rule variants, applied to the published judgments
    def final_alt(r, cap="cap", dq_pen=15.0, w=(0.40, 0.35, 0.25), wa=0.25, scr_line=None):
        comp = {k: F(r, k) for k in COMPONENTS}
        fl = flags_of(r)
        if scr_line is not None and r["paper_id"] in SCR:
            s = SCR[r["paper_id"]]
            fl = fl - SC_FLAGS
            if s > scr_line:
                fl.add("EXCESSIVE_SELF_CITATION")
            elif s >= 0.20:
                fl.add("ELEVATED_SELF_CITATION")
        ii = w[0] * comp["formalism"] + w[1] * comp["citation_integrity"] + w[2] * comp["structural_integrity"]
        composite = (1 - wa) * ii + wa * comp["artifact_availability"]
        dq = rs.disqualifying(fl, lvl(r))
        if dq and cap == "cap":
            final = min(composite, rs.DISQUALIFYING_CAP)
        else:
            final = composite - rs.HIGH_SEVERITY_PENALTY * len(fl & rs.HIGH_SEVERITY_FLAGS) \
                - rs.MEDIUM_SEVERITY_PENALTY * len(fl & rs.MEDIUM_SEVERITY_FLAGS)
            if dq and cap == "deduct":
                final -= dq_pen * len(dq)
        return max(0.0, min(100.0, final)), bool(dq)

    variants = collections.OrderedDict([
        ("published", {}),
        ("cap_as_minus15", {"cap": "deduct", "dq_pen": 15.0}),
        ("no_cap_no_penalty", {"cap": "none"}),
        ("scr_line_25", {"scr_line": 0.25}),
        ("scr_line_35", {"scr_line": 0.35}),
        ("scr_line_40", {"scr_line": 0.40}),
        ("scr_line_50", {"scr_line": 0.50}),
        ("weights_equal", {"w": (1 / 3, 1 / 3, 1 / 3)}),
        ("weights_30_35_35", {"w": (0.30, 0.35, 0.35)}),
        ("artifact_015", {"wa": 0.15}),
        ("artifact_035", {"wa": 0.35}),
    ])
    out["B"] = {}
    for name, kw in variants.items():
        res = [final_alt(r, **kw) for r in rows]
        fin = [x[0] for x in res]
        bands = [rs.classify(round(x, 2)) for x in fin]
        cnt = collections.Counter(bands)
        out["B"][name] = {"bands": {b: cnt.get(b, 0) for b in BANDS},
                          "disqualified": sum(x[1] for x in res),
                          "changed_band": sum(a != b for a, b in zip(bands, band0)),
                          "spearman": round(spearman(pub, fin), 3)}
    assert out["B"]["published"]["changed_band"] == 0

    # --- C. model sensitivity, from the three test-retest runs
    def load(d):
        o = {}
        for path in glob.glob(str(Path(d) / "*.json")):
            b = json.load(open(path, encoding="utf-8"))
            for p in b["papers"]:
                o[(b["batch_id"], p["paper"]["source_file"])] = p
        return o
    runs = [load(Path(fw) / "journal-analysis" / "ROMJIST_2026-10-04"),
            load(Path(fw) / "reliability" / "runs" / "run2"), load(Path(fw) / "reliability" / "runs" / "run3")]
    sample = list(csv.DictReader(open(Path(fw) / "reliability" / "sample.csv", encoding="utf-8")))
    dq_same = band_same3 = 0
    pair_same = pair_n = 0
    splits, two_step, diffs = [], 0, []
    for s in sample:
        recs = [R[(s["batch_id"], s["source_file"])] for R in runs]
        bands = [p["verdict"]["classification"] for p in recs]
        dqs = [p["verdict"]["disqualified"] for p in recs]
        fins = [float(p["scores"]["final"]) for p in recs]
        dq_same += len(set(dqs)) == 1
        band_same3 += len(set(bands)) == 1
        if len(set(bands)) > 1:
            span = max(map(BANDS.index, bands)) - min(map(BANDS.index, bands))
            splits.append(span)
            two_step += span > 1
        for a, b in itertools.combinations(range(3), 2):
            pair_n += 1
            pair_same += bands[a] == bands[b]
            if not dqs[a] and not dqs[b]:
                diffs.append(fins[a] - fins[b])
    rng = random.Random(20261018)
    sym = diffs + [-d for d in diffs]
    unc = [r for r in rows if r["disqualified"] != "True"]
    probs = []
    for r in unc:
        f0 = F(r, "final")
        b0 = rs.classify(f0)
        probs.append(sum(rs.classify(round(max(0.0, min(100.0, f0 + rng.choice(sym))), 2)) != b0
                         for _ in range(4000)) / 4000)
    out["C"] = {"sample": len(sample), "disqualification_same_all_three": dq_same,
                "band_same_all_three": band_same3, "pairwise_band_same": pair_same, "pairs": pair_n,
                "band_disagreements": len(splits), "two_band_disagreements": two_step,
                "uncapped_pairwise_diffs": len(diffs),
                "expected_band_change_uncapped": round(st.mean(probs), 3),
                "expected_band_change_corpus": round(sum(probs) / len(rows), 3),
                "uncapped_with_p_ge_025": sum(p >= 0.25 for p in probs)}
    return out


TABLE5 = [
    ("Published rules", "published"),
    ("Cap replaced by -15 per flag", "cap_as_minus15"),
    ("No cap, no deduction (finding counted once)", "no_cap_no_penalty"),
    ("Self-citation line at 25%", "scr_line_25"),
    ("Self-citation line at 35%", "scr_line_35"),
    ("Self-citation line at 40%", "scr_line_40"),
    ("Self-citation line at 50%", "scr_line_50"),
    ("Equal integrity weights", "weights_equal"),
    ("Integrity weights 30/35/35", "weights_30_35_35"),
    ("Artifact weight 0.15", "artifact_015"),
    ("Artifact weight 0.35", "artifact_035"),
]


def table5_rows(out):
    """Table 5 of the manuscript: band counts, capped papers, band changes, Spearman rho."""
    rows = []
    for label, key in TABLE5:
        v = out["B"][key]
        rows.append({"rule_variant": label,
                     **{b.lower(): v["bands"][b] for b in BANDS},
                     "capped": 0 if key in ("cap_as_minus15", "no_cap_no_penalty") else v["disqualified"],
                     "changed_band": "" if key == "published" else v["changed_band"],
                     "spearman_rho": f"{v['spearman']:.2f}"})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--output", type=Path, default=REPO / "scripts" / "output" / "tables")
    args = ap.parse_args()
    out = compute(args.repo)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "classification_stability.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    rows = table5_rows(out)
    with (args.output / "table5_rule_sensitivity.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
