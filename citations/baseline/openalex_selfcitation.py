"""Reference-side self-citation in computer science journal articles, from OpenAlex.

RUIN's self-citation ratio (SCR) is the share of a paper's references that
include at least one of its own authors. Published self-citation rates are
mostly citing-side (the share of an author's received citations), so they do
not calibrate SCR. This script measures SCR's distribution in the field: a
random sample of 2,000 computer science journal articles (OpenAlex field 17,
2010-2025, at least ten references), each reference counted as a
self-citation when it shares an OpenAlex author ID with the citing article.

    python citations/baseline/openalex_selfcitation.py --n 2000 --seed 20261018

Writes citations/baseline/openalex_scr.csv (one row per sampled article) and
citations/baseline/openalex_scr_summary.json (percentiles, and the share of
articles above the 15%, 20% and 30% lines). Standard library only. Author
identities rest on OpenAlex's disambiguation, and references OpenAlex could not
resolve are left out of both numerator and denominator.
"""

import argparse
import csv
import json
import statistics as st
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.openalex.org/works"
FILTER = ("primary_topic.field.id:fields/17,type:article,publication_year:2010-2025,"
          "primary_location.source.type:journal,referenced_works_count:>9")


def get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def author_ids(work: dict) -> set:
    return {a["author"]["id"] for a in work.get("authorships") or [] if a.get("author", {}).get("id")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261018)
    args = ap.parse_args()

    sample = []
    page = 1
    while len(sample) < args.n:
        data = get({"filter": FILTER, "sample": args.n, "seed": args.seed, "per_page": 100, "page": page,
                    "select": "id,publication_year,authorships,referenced_works"})
        if not data["results"]:
            break
        sample += data["results"]
        page += 1
    sample = sample[:args.n]
    print(f"sampled {len(sample)} articles", flush=True)

    refs = sorted({w for s in sample for w in s.get("referenced_works") or []})
    authors_of = {}
    for i in range(0, len(refs), 100):
        chunk = refs[i:i + 100]
        ids = "|".join(r.rsplit("/", 1)[-1] for r in chunk)
        data = get({"filter": f"openalex:{ids}", "per_page": 100, "select": "id,authorships"})
        for w in data["results"]:
            authors_of[w["id"]] = author_ids(w)
        if i % 10000 == 0:
            print(f"  references resolved {len(authors_of)}/{len(refs)}", flush=True)

    rows = []
    for s in sample:
        own = author_ids(s)
        resolved = [r for r in s.get("referenced_works") or [] if r in authors_of]
        if len(resolved) < 10 or not own:
            continue
        self_refs = sum(bool(authors_of[r] & own) for r in resolved)
        rows.append({"id": s["id"], "year": s["publication_year"], "n_refs": len(resolved),
                     "n_self": self_refs, "scr": round(self_refs / len(resolved), 4)})
    with (HERE / "openalex_scr.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    scr = sorted(r["scr"] for r in rows)
    q = st.quantiles(scr, n=100)
    summary = {
        "filter": FILTER, "seed": args.seed, "sampled": len(sample), "analysed": len(rows),
        "median": round(st.median(scr), 4), "mean": round(st.mean(scr), 4),
        "percentiles": {p: round(q[p - 1], 4) for p in (50, 75, 80, 85, 90, 95, 99)},
        "share_above": {f"{int(t * 100)}%": round(sum(x > t for x in scr) / len(scr), 4) for t in (0.15, 0.20, 0.30)},
        "share_at_least_20%": round(sum(x >= 0.20 for x in scr) / len(scr), 4),
        "percentile_of_line": {f"{int(t * 100)}%": round(100 * sum(x <= t for x in scr) / len(scr), 1)
                               for t in (0.15, 0.20, 0.30)},
    }
    (HERE / "openalex_scr_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
