"""Join a Web of Science export onto the RUIN score table.

Why WoS and not OpenAlex/Crossref: ROMJIST did not register DOIs before 2023.
Crossref holds 120 ROMJIST DOIs, all 2023 or later; OpenAlex holds 133 works, of
which only 6 match a pre-2023 RUIN paper. Title-matching against OpenAlex recovers
93% of the 2023-2025 slice but 1.8% of everything earlier, so OpenAlex can reach
88 of the 415 papers. ROMJIST has been in SCIE since 2008, so Web of Science is the
only source that covers 2010-2022 -- 79% of the corpus and all of the papers old
enough to have accumulated citations.

Getting the export (needs a WoS session; UPT and UAV Arad both have access
through Anelis Plus):
  1. Web of Science -> Documents -> Advanced Search
  2. Query:  SO=("ROMANIAN JOURNAL OF INFORMATION SCIENCE AND TECHNOLOGY")
     optionally AND PY=(2010-2025)
  3. Export -> Excel or Tab delimited file
  4. Record Content: choose a set that includes "Times Cited" --
     "Full Record" works, or Custom with at least:
        Article Title, Publication Year, Volume, Issue, Beginning Page,
        Times Cited (WoS Core), Times Cited (All Databases), DOI
  5. Records: 1 to 500  (the corpus is 415, so one export covers it)

Then:
    python merge_wos_citations.py wos_export.xls ruin_scores.csv merged.csv

Handles both the two-letter-tag tab-delimited format (TI/PY/TC/Z9/...) and the
Excel export's long column names.
"""

import csv
import re
import sys
import difflib
from pathlib import Path

# WoS column aliases -> our canonical names. Both export flavours are covered.
ALIASES = {
    "title": ["TI", "Article Title", "Title"],
    "year": ["PY", "Publication Year"],
    "volume": ["VL", "Volume"],
    "issue": ["IS", "Issue"],
    "start_page": ["BP", "Beginning Page", "Start Page"],
    "doi": ["DI", "DOI"],
    "tc_core": ["TC", "Times Cited, WoS Core", "Times Cited"],
    "tc_all": ["Z9", "Times Cited, All Databases"],
}


def norm(s):
    """Aggressive title key: lowercase, strip everything but alphanumerics."""
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def read_wos(path):
    """Read a WoS export: a real .xlsx workbook, or tab/comma delimited text.

    WoS's "Export -> Excel" produces a genuine .xlsx, which is a zip archive and
    cannot be decoded as text, so that case is handled first.
    """
    if Path(path).suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            sys.exit(
                f"{path} is an Excel workbook and openpyxl is not installed.\n"
                "Either  pip install openpyxl  or re-export from WoS as "
                '"Tab delimited file".'
            )
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        it = ws.iter_rows(values_only=True)
        try:
            header = [("" if h is None else str(h).strip()) for h in next(it)]
        except StopIteration:
            sys.exit(f"{path}: empty worksheet")
        rows = []
        for raw_row in it:
            if not any(v is not None and str(v).strip() for v in raw_row):
                continue
            rows.append({
                h: ("" if v is None else str(v))
                for h, v in zip(header, raw_row) if h
            })
    else:
        raw = Path(path).read_bytes()
        for enc in ("utf-8-sig", "utf-16", "utf-8", "latin-1"):
            try:
                text = raw.decode(enc)
                if "\t" in text or "," in text:
                    break
            except UnicodeDecodeError:
                continue
        else:
            sys.exit(f"could not decode {path}")

        delim = "\t" if text.count("\t") > text.count(",") else ","
        rows = list(csv.DictReader(text.splitlines(), delimiter=delim))

    if not rows:
        sys.exit(f"{path}: no rows parsed")

    headers = list(rows[0].keys())
    colmap = {}
    for canon, opts in ALIASES.items():
        for o in opts:
            hit = next((h for h in headers if h and h.strip().lower() == o.lower()), None)
            if hit:
                colmap[canon] = hit
                break

    if "title" not in colmap:
        sys.exit(f"{path}: no title column found. Headers seen: {headers[:20]}")
    if "tc_core" not in colmap and "tc_all" not in colmap:
        sys.exit(f"{path}: no Times Cited column. Re-export including Times Cited.\n"
                 f"Headers seen: {headers[:20]}")

    out = []
    for r in rows:
        rec = {c: (r.get(h) or "").strip() for c, h in colmap.items()}
        if rec.get("title"):
            out.append(rec)
    return out, colmap


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    wos_path, ruin_path = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else "merged.csv"

    wos, colmap = read_wos(wos_path)
    print(f"WoS export: {len(wos)} records; columns matched: {sorted(colmap)}")

    ruin = list(csv.DictReader(open(ruin_path, encoding="utf-8")))
    print(f"RUIN table: {len(ruin)} papers")

    index = {}
    for w in wos:
        index.setdefault(norm(w["title"]), w)
    keys = list(index)

    exact = fuzzy = prefix = 0
    unmatched = []
    for r in ruin:
        k = norm(r["title"])
        hit, how = index.get(k), "exact"
        if hit:
            exact += 1
        else:
            m = difflib.get_close_matches(k, keys, n=1, cutoff=0.90)
            if m:
                hit, how = index[m[0]], "fuzzy"
                fuzzy += 1
            else:
                # WoS sometimes indexes a paper under its main title while the
                # PDF carries title plus subtitle, which drops the similarity
                # below the fuzzy cutoff even though the match is certain. Accept
                # a prefix match when the shorter title is long enough to be
                # unambiguous and it resolves to exactly one WoS record.
                cands = [
                    key for key in keys
                    if len(key) >= 30 and k.startswith(key)
                ]
                if len(cands) == 1:
                    hit, how = index[cands[0]], "prefix"
                    prefix += 1
                else:
                    unmatched.append(r)
                    how = ""
        # A blank citation cell in WoS means zero, but an unmatched paper means
        # unknown. Keep those distinct -- collapsing them to 0 biases the result.
        if hit:
            tc = hit.get("tc_core") or hit.get("tc_all") or "0"
            r["citations"] = int(re.sub(r"[^0-9]", "", tc) or 0)
            r["wos_doi"] = hit.get("doi", "")
        else:
            r["citations"] = ""
            r["wos_doi"] = ""
        r["match"] = how

    n = len(ruin)
    print(f"  exact title match : {exact}")
    print(f"  fuzzy (>=0.90)    : {fuzzy}")
    print(f"  title-prefix      : {prefix}")
    print(f"  MATCHED           : {exact + fuzzy + prefix}  ({(exact + fuzzy + prefix) / n * 100:.1f}%)")
    print(f"  unmatched         : {len(unmatched)}")

    if unmatched:
        print("\n  unmatched titles (resolve these by hand before analysing):")
        for r in unmatched[:25]:
            print(f"    {r['year']}  {r['title'][:88]}")
        if len(unmatched) > 25:
            print(f"    ... and {len(unmatched) - 25} more")

    fields = list(ruin[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(ruin)
    print(f"\nwrote {out_path}")

    matched = [r for r in ruin if r["citations"] != ""]
    if matched:
        c = sorted(int(r["citations"]) for r in matched)
        zeros = sum(1 for x in c if x == 0)
        print(f"citations on matched: min={c[0]} median={c[len(c)//2]} "
              f"mean={sum(c)/len(c):.1f} max={c[-1]} zeros={zeros}/{len(c)}")


if __name__ == "__main__":
    main()
