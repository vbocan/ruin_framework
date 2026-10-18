"""Computed topical relevance of self-citations, against the model's judgment.

RUIN's IRRELEVANT_SELF_CITATION flag rests on a relevance judgment the model
makes while reading the paper (manuscript, Section 3.1.5). This script computes
relevance instead: SPECTER2 (allenai/specter2_base, CLS embedding) of the citing
paper's title and abstract, the same for the title of every reference GROBID
extracted (../references/), and their cosine similarity. It then asks whether
the self-citations the model judged irrelevant are those the embedding places
farthest from the citing paper, compared with the paper's other self-citations
and with its references to other authors.

Self-citations are the references ../self_citation_check.py identified. The
references a flag names ("[22]", "[34-53]") are read as positions in the GROBID
list, and only those that are also self-citations count as flagged.

    docker build -t ruin-specter2 citations/relevance
    docker run --rm -v "$PWD:/work" -w /work ruin-specter2 \
        python citations/relevance/specter2_relevance.py --run journal-analysis/ROMJIST_2026-10-04

Writes specter2_relevance.csv (one row per reference with a title) and
specter2_relevance.json (the comparison).
"""

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from self_citation_check import listed_references  # noqa: E402

MODEL = "allenai/specter2_base"


def embed(texts, tok, model, batch=32):
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], padding=True, truncation=True, max_length=512, return_tensors="pt")
            out.append(model(**enc).last_hidden_state[:, 0, :])
    return torch.nn.functional.normalize(torch.cat(out), dim=1)


def auc(low, high):
    """P(a value from `high` exceeds one from `low`), ties counted half."""
    if not low or not high:
        return None
    wins = sum((h > l) + 0.5 * (h == l) for l in low for h in high)
    return round(wins / (len(low) * len(high)), 3)


def describe(xs):
    if not xs:
        return None
    return {"n": len(xs), "median": round(st.median(xs), 3), "mean": round(st.mean(xs), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args()

    selfref = {(r["batch_id"], r["source_file"]): {int(x) for x in r["self_ref_indices"].split()}
               for r in csv.DictReader((HERE.parent / "self_citation_check.csv").open(encoding="utf-8"))}
    citing, rows = [], []
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        refs_by_pdf = json.loads((HERE.parent / "references" / f'{batch["batch_id"]}.json').read_text(encoding="utf-8"))
        for p in batch["papers"]:
            flags = set(p.get("flags") or [])
            if flags & {"EDITORIAL", "PDF_CORRUPTED"}:
                continue
            key = (batch["batch_id"], p["paper"]["source_file"])
            own = selfref.get(key, set())
            flagged = set()
            if "IRRELEVANT_SELF_CITATION" in flags:
                flagged = listed_references((p.get("flag_details") or {}).get("IRRELEVANT_SELF_CITATION", "")) & own
            citing.append(f'{p["paper"].get("title", "")}. {p["paper"].get("abstract", "")}')
            for i, r in enumerate(refs_by_pdf.get(key[1]) or [], 1):
                if r["title"]:
                    rows.append({"batch_id": key[0], "source_file": key[1], "paper_id": p["paper_id"], "ref": i,
                                 "title": r["title"], "self_citation": int(i in own),
                                 "model_irrelevant": int(i in flagged),
                                 "paper_flagged": int("IRRELEVANT_SELF_CITATION" in flags),
                                 "_paper": len(citing) - 1})

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).eval()
    pe = embed(citing, tok, model)
    rel = embed([r["title"] for r in rows], tok, model)
    for k, r in enumerate(rows):
        r["similarity"] = round(float(pe[r["_paper"]] @ rel[k]), 4)

    # Within-paper percentile of each reference's similarity (0 = least similar reference of its paper).
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["_paper"], []).append(r)
    for group in by_paper.values():
        ordered = sorted(group, key=lambda r: r["similarity"])
        for rank, r in enumerate(ordered):
            r["within_paper_percentile"] = round(100 * rank / max(len(ordered) - 1, 1), 1)

    fields = ["batch_id", "source_file", "paper_id", "ref", "title", "similarity", "within_paper_percentile",
              "self_citation", "model_irrelevant", "paper_flagged"]
    with (HERE / "specter2_relevance.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    flagged = [r for r in rows if r["model_irrelevant"]]
    self_other = [r for r in rows if r["self_citation"] and not r["model_irrelevant"]]
    nonself = [r for r in rows if not r["self_citation"]]
    flagged_papers = {r["_paper"] for r in flagged}
    same_paper_self = [r["similarity"] for r in self_other if r["_paper"] in flagged_papers]
    lowest = sum(min(by_paper[pi], key=lambda r: r["similarity"])["model_irrelevant"] == 1 for pi in flagged_papers)
    within = []  # per paper: P(another self-citation of the paper is more similar than a flagged one)
    for pi in sorted(flagged_papers):
        a = [r["similarity"] for r in by_paper[pi] if r["model_irrelevant"]]
        b = [r["similarity"] for r in by_paper[pi] if r["self_citation"] and not r["model_irrelevant"]]
        if a and b:
            within.append(auc(a, b))
    counts = {}
    for r in flagged:
        counts[r["_paper"]] = counts.get(r["_paper"], 0) + 1
    largest = max(counts, key=counts.get) if counts else None
    rest = [r for r in rows if r["_paper"] != largest]
    summary = {
        "model": MODEL, "papers": len(citing), "references_with_title": len(rows),
        "self_citations": len(flagged) + len(self_other), "papers_with_flag": len({r["paper_id"] for r in rows if r["paper_flagged"]}),
        "flagged_references_matched": len(flagged), "papers_with_matched_flagged_reference": len(flagged_papers),
        "similarity": {"flagged_irrelevant": describe([r["similarity"] for r in flagged]),
                       "other_self_citations": describe([r["similarity"] for r in self_other]),
                       "other_self_citations_same_papers": describe(same_paper_self),
                       "references_to_others": describe([r["similarity"] for r in nonself])},
        "auc_other_self_above_flagged": auc([r["similarity"] for r in flagged], [r["similarity"] for r in self_other]),
        "auc_same_paper_self_above_flagged": auc([r["similarity"] for r in flagged], same_paper_self),
        "auc_other_self_above_flagged_without_largest_paper": {
            "flagged_in_largest_paper": counts.get(largest, 0),
            "auc": auc([r["similarity"] for r in rest if r["model_irrelevant"]],
                       [r["similarity"] for r in rest if r["self_citation"] and not r["model_irrelevant"]])},
        "within_paper_auc": {"papers": len(within), "mean": round(st.mean(within), 3) if within else None,
                             "above_0_5": sum(x > 0.5 for x in within)},
        "auc_self_above_references_to_others": auc([r["similarity"] for r in nonself],
                                                   [r["similarity"] for r in flagged + self_other]),
        "flagged_within_paper_percentile": describe([r["within_paper_percentile"] for r in flagged]),
        "flagged_in_bottom_quarter_of_paper": {"n": sum(r["within_paper_percentile"] <= 25 for r in flagged),
                                               "of": len(flagged)},
        "papers_whose_least_similar_reference_is_flagged": {"n": lowest, "of": len(flagged_papers)},
    }
    (HERE / "specter2_relevance.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
