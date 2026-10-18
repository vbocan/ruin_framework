"""The OpenAlex self-citation ratio of the ROMJIST articles OpenAlex indexes.

openalex_selfcitation.py measures the reference-side self-citation ratio (SCR)
of computer science journal articles through OpenAlex author identifiers. This
script measures the same quantity, the same way, for the ROMJIST articles that
OpenAlex holds with at least ten references (in practice 2023-2025), so that
the corpus and the field are compared on one method. It also matches those
articles to the corpus records by DOI and sets the OpenAlex ratio beside the
name-matched count of ../self_citation_check.py, which measures how far the two
counting methods differ.

    python citations/baseline/openalex_romjist.py --run journal-analysis/ROMJIST_2026-10-04

Writes openalex_romjist.csv and openalex_romjist_summary.json. Standard library only.
"""

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

import classification_stability as cs  # noqa: E402  (Spearman)
from openalex_selfcitation import author_ids, get  # noqa: E402

SOURCE = "S151779546"  # Romanian Journal of Information Science and Technology


def norm_doi(doi):
    return (doi or "").lower().replace("https://doi.org/", "").strip()


def norm_title(title):
    return "".join(c for c in (title or "").lower() if c.isalnum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args()

    works, page = [], 1
    while True:
        data = get({"filter": f"primary_location.source.id:{SOURCE},publication_year:2010-2025,referenced_works_count:>9",
                    "per_page": 100, "page": page, "select": "id,doi,display_name,publication_year,authorships,referenced_works"})
        works += data["results"]
        if len(data["results"]) < 100:
            break
        page += 1
    refs = sorted({w for s in works for w in s.get("referenced_works") or []})
    authors_of = {}
    for i in range(0, len(refs), 100):
        ids = "|".join(r.rsplit("/", 1)[-1] for r in refs[i:i + 100])
        for w in get({"filter": f"openalex:{ids}", "per_page": 100, "select": "id,authorships"})["results"]:
            authors_of[w["id"]] = author_ids(w)

    code = {}
    for r in csv.DictReader((HERE.parent / "self_citation_check.csv").open(encoding="utf-8")):
        code[(r["batch_id"], r["source_file"])] = r
    by_doi, by_title, corpus_recent = {}, {}, []
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        for p in batch["papers"]:
            row = code.get((batch["batch_id"], p["paper"]["source_file"]))
            if row is None:
                continue
            if norm_doi(p["paper"].get("doi")):
                by_doi[norm_doi(p["paper"].get("doi"))] = row
            by_title[norm_title(p["paper"].get("title"))] = row
            if 2023 <= int(batch["batch_id"][:4]) <= 2025 and row["scr_code"] != "":
                corpus_recent.append(float(row["scr_code"]))

    rows = []
    for s in works:
        own = author_ids(s)
        resolved = [r for r in s.get("referenced_works") or [] if r in authors_of]
        if len(resolved) < 10 or not own:
            continue
        n_self = sum(bool(authors_of[r] & own) for r in resolved)
        match = by_doi.get(norm_doi(s.get("doi"))) or by_title.get(norm_title(s.get("display_name")))
        rows.append({"id": s["id"], "doi": norm_doi(s.get("doi")), "year": s["publication_year"],
                     "n_refs": len(resolved), "n_self": n_self, "scr": round(n_self / len(resolved), 4),
                     "paper_id": match["paper_id"] if match else "",
                     "scr_code": match["scr_code"] if match else "",
                     "model_flag": match["model_flag"] if match else ""})
    with (HERE / "openalex_romjist.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    field = json.loads((HERE / "openalex_scr_summary.json").read_text(encoding="utf-8"))
    field_scr = sorted(float(r["scr"]) for r in csv.DictReader((HERE / "openalex_scr.csv").open(encoding="utf-8")))
    scr = [r["scr"] for r in rows]
    matched = [r for r in rows if r["scr_code"] != ""]
    a, b = [r["scr"] for r in matched], [float(r["scr_code"]) for r in matched]
    summary = {
        "source": SOURCE, "articles_listed": len(works), "analysed": len(rows),
        "years": sorted({r["year"] for r in rows}),
        "median": round(st.median(scr), 4), "mean": round(st.mean(scr), 4),
        "share_at_least_20%": round(sum(x >= 0.20 for x in scr) / len(scr), 4),
        "share_above_30%": round(sum(x > 0.30 for x in scr) / len(scr), 4),
        "field_median": field["median"], "field_share_at_least_20%": field["share_at_least_20%"],
        "field_share_above_30%": field["share_above_30%"] if "share_above_30%" in field else field["share_above"]["30%"],
        "median_field_percentile_of_romjist_articles": round(st.median(
            [100 * sum(f <= x for f in field_scr) / len(field_scr) for x in scr]), 1),
        "corpus_2023_2025_name_matching": {
            "n": len(corpus_recent), "median": round(st.median(corpus_recent), 4),
            "share_at_least_20%": round(sum(x >= 0.20 for x in corpus_recent) / len(corpus_recent), 4),
            "share_above_30%": round(sum(x > 0.30 for x in corpus_recent) / len(corpus_recent), 4)},
        "matched_to_corpus": {"n": len(matched),
                              "spearman_openalex_vs_name_matching": round(cs.spearman(a, b), 3) if len(matched) > 2 else None,
                              "median_openalex": round(st.median(a), 4) if a else None,
                              "median_name_matching": round(st.median(b), 4) if b else None,
                              "mean_difference_name_minus_openalex": round(st.mean(y - x for x, y in zip(a, b)), 4) if a else None},
    }
    (HERE / "openalex_romjist_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
