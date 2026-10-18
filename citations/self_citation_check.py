"""A deterministic count of each paper's self-citation ratio, against the model's.

RUIN's self-citation flags are raised by the assessing model, which counts the
paper's self-references while reading it (Section 3.2.2 of the manuscript). This
script counts them without a model: GROBID (references/extract_references.py)
splits each PDF's reference list into references, each reference's raw string
is matched against the paper's own authors, and the thresholds of Section 3.1.5
are applied in code.

The raw strings are used, not GROBID's parsed author fields, because ROMJIST
sets author names in small capitals with Romanian and Czech diacritics: text
extraction detaches the diacritic ("VINT ¸AN L.") and GROBID then splits the
name in the wrong place. repair() rejoins such names, deterministically.

Matching: each reference is cut into segments at commas, semicolons, colons and
"and" (a segment of initials alone joins the one before it, for the "Pan, L."
style). A segment matches a paper author when one of its name tokens (any
all-capitals word, or a capitalised word next to initials) equals the author's
surname or a hyphenated part of it after folding accents, and the segment's
initials, if it has any, include one of the author's initials. An all-capitals
token ending in a capital and a period ("SERBANB.", where extraction lost the
space) is also tried as surname plus initial. A reference that matches any
author counts as a self-citation.

    python citations/self_citation_check.py --run journal-analysis/ROMJIST_2026-10-04

Writes self_citation_check.csv (one row per research paper) and
self_citation_check.json (agreement with the model's flags, recorded ratios and
listed references). Standard library only.
"""

import argparse
import csv
import json
import re
import statistics as st
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import classification_stability as cs  # noqa: E402  (recorded-ratio parser, Spearman)

SC = ("EXCESSIVE_SELF_CITATION", "ELEVATED_SELF_CITATION")
MARKS = "¸˘ˆ´¨˜ˇ˝˛˙̀-ͯ"  # detached accents
LATIN = "À-ɏ"                                                            # accented Latin letters
HYPHENS = "\\-\u2010\u2011"
PARTICLES = {"de", "da", "di", "del", "della", "der", "den", "van", "von", "la", "le", "du", "dos", "al", "el"}
INITIALS = re.compile(r"^(?:[A-Z][a-z]?[.\-]+)*[A-Z][a-z]?\.?$")  # "L.", "M.G.", "R.-D", "Gh."


def fold(text):
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if c.isascii() and c.isalpha()).lower()


def repair(raw):
    """Rejoin names that PDF text extraction split around a diacritic."""
    s = unicodedata.normalize("NFC", raw or "")
    s = re.sub(rf"\s+[{MARKS}](?=\w)", "", s)                  # "VINT ¸AN"  -> "VINTAN"
    s = re.sub(rf"[{MARKS}]", "", s)
    s = re.sub(rf"(?<=\w)\s+(?=[{LATIN}])", "", s)              # "P ȂUN", "ROHL Í ČEK" -> "PȂUN", "ROHLÍČEK"
    s = re.sub(rf"(?<=[{LATIN}])\s+(?=[A-Z]+(?![.\w]))", "", s)  # "MAŘÍ K O." -> "MAŘÍK O."
    return s


def is_initials(token):
    return bool(INITIALS.match(token)) and ("." in token or len(token) == 1 or "-" in token)


def initials_of(token):
    return {fold(x)[:1] for x in re.split(rf"[.{HYPHENS}]", token) if fold(x)}


def author_keys(name):
    """(surname variants, initials) for a name written 'Forename [Middle] Surname'."""
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    if not parts:
        return set(), set()
    surname = parts[-1]
    variants = {fold(surname)} | {fold(x) for x in re.split(rf"[{HYPHENS}]", surname)}
    given = [p for p in parts[:-1] if fold(p) not in PARTICLES]
    initials = set().union(*(initials_of(g) for g in given)) if given else set()
    return {v for v in variants if len(v) >= 2}, initials


def segment_matches(segment, authors):
    tokens = [t for t in (t.strip("()[]") for t in segment.split()) if t]
    initials = set().union(*(initials_of(t) for t in tokens if is_initials(t)))
    for t in tokens:
        letters = [c for c in t if c.isalpha()]
        if len(letters) < 2 or is_initials(t):
            continue
        caps = all(c.isupper() for c in letters)
        candidates = []
        if caps or (letters[0].isupper() and initials):
            candidates.append((t, initials))
        if caps and len(letters) >= 4 and re.search(r"[A-Z]\.$", t):  # "SERBANB." read as "SERBAN B."
            candidates.append((t[:-2], initials | {fold(t[-2])}))
        for name, inits in candidates:
            keys = {fold(name)} | {fold(x) for x in re.split(rf"[{HYPHENS}]", name)}
            for variants, own in authors:
                if keys & variants and (not inits or not own or inits & own):
                    return True
    return False


def is_self_citation(raw, authors):
    """Cut the repaired reference into name segments; an initials-only segment
    ("Pan, L.") belongs to the segment before it."""
    segments = []
    for seg in re.split(r",|;|:|\band\b|&", repair(raw)):
        tokens = [t.strip("()[]") for t in seg.split()]
        if not tokens:
            continue
        if segments and all(is_initials(t) for t in tokens):
            segments[-1] += " " + seg
        else:
            segments.append(seg)
    return any(segment_matches(seg, authors) for seg in segments)


def listed_references(details):
    """Reference numbers the model named in its flag detail: [3], [1]-[11], [4-7]."""
    found = set()
    for a, b in re.findall(r"\[(\d+)\]\s*[-–]\s*\[(\d+)\]", details):
        found |= set(range(int(a), int(b) + 1))
    for a, b in re.findall(r"\[(\d+)\s*[-–]\s*(\d+)\]", details):
        found |= set(range(int(a), int(b) + 1))
    found |= {int(n) for n in re.findall(r"\[(\d+)\]", details)}
    return found


def category(ratio):
    if ratio is None:
        return None
    if ratio > 0.30:
        return "excessive"
    if ratio >= 0.20:
        return "elevated"
    return "none"


def share(n, d):
    return {"n": n, "of": d, "share": round(n / d, 3) if d else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        refs_file = HERE / "references" / f'{batch["batch_id"]}.json'
        refs_by_pdf = json.loads(refs_file.read_text(encoding="utf-8")) if refs_file.exists() else {}
        for p in batch["papers"]:
            flags = set(p.get("flags") or [])
            if flags & {"EDITORIAL", "PDF_CORRUPTED"}:
                continue
            refs = refs_by_pdf.get(p["paper"]["source_file"])
            authors = [author_keys(a) for a in p["paper"].get("authors") or []]
            model_flag = next((f for f in SC if f in flags), "")
            details = (p.get("flag_details") or {}).get(model_flag, "")
            stated = cs.scr_from_details(details) if details else None
            m = re.search(r"(?:of|/|out of)\s+(\d+)", details) if details else None
            listed = listed_references(details) if details else set()
            row = {"batch_id": batch["batch_id"], "source_file": p["paper"]["source_file"], "paper_id": p["paper_id"],
                   "n_refs_grobid": len(refs) if refs is not None else "", "n_self_grobid": "", "scr_code": "",
                   "self_ref_indices": "", "model_flag": model_flag,
                   "model_ratio": round(stated, 4) if stated is not None else "",
                   "model_n_refs": int(m.group(1)) if m else "",
                   "model_listed_refs": " ".join(map(str, sorted(listed)))}
            if refs:
                idx = [i + 1 for i, r in enumerate(refs) if is_self_citation(r["raw"], authors)]
                row["n_self_grobid"] = len(idx)
                row["scr_code"] = round(len(idx) / len(refs), 4)
                row["self_ref_indices"] = " ".join(map(str, idx))
            rows.append(row)

    with (HERE / "self_citation_check.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    usable = [r for r in rows if r["scr_code"] != "" and r["n_refs_grobid"] >= 3]
    names = {"EXCESSIVE_SELF_CITATION": "excessive", "ELEVATED_SELF_CITATION": "elevated"}
    cats = ("excessive", "elevated", "none")
    confusion = {m: {c: sum(1 for r in usable if names.get(r["model_flag"], "none") == m and category(r["scr_code"]) == c)
                     for c in cats} for m in cats}
    agree = sum(confusion[c][c] for c in cats)
    flagged_model = {r["paper_id"] for r in usable if r["model_flag"]}
    flagged_code = {r["paper_id"] for r in usable if category(r["scr_code"]) != "none"}
    exc_model = {r["paper_id"] for r in usable if names.get(r["model_flag"]) == "excessive"}
    exc_code = {r["paper_id"] for r in usable if category(r["scr_code"]) == "excessive"}
    with_ratio = [r for r in usable if r["model_ratio"] != ""]
    diffs = [abs(r["scr_code"] - r["model_ratio"]) for r in with_ratio]
    with_n = [r for r in usable if r["model_n_refs"] != ""]
    with_list = [r for r in usable if r["model_listed_refs"]]
    sets = [(set(r["model_listed_refs"].split()), set(r["self_ref_indices"].split())) for r in with_list]
    jacc = [len(a & b) / len(a | b) for a, b in sets]
    scr_all = [r["scr_code"] for r in usable]
    summary = {
        "papers": len(rows), "with_grobid_references": len(usable),
        "code_scr_distribution": {"median": round(st.median(scr_all), 4), "mean": round(st.mean(scr_all), 4),
                                  "share_at_least_20%": round(sum(x >= 0.20 for x in scr_all) / len(scr_all), 4),
                                  "share_above_30%": round(sum(x > 0.30 for x in scr_all) / len(scr_all), 4)},
        "category_confusion_model_rows_code_columns": confusion,
        "category_agreement": share(agree, len(usable)),
        "flag_vs_no_flag": {"model": len(flagged_model), "code": len(flagged_code),
                            "both": len(flagged_model & flagged_code),
                            "agreement": share(len(usable) - len(flagged_model ^ flagged_code), len(usable))},
        "excessive": {"model": len(exc_model), "code": len(exc_code), "both": len(exc_model & exc_code)},
        "stated_ratio_vs_code": {
            "n": len(with_ratio),
            "mean_abs_diff": round(st.mean(diffs), 4) if diffs else None,
            "within_0_05": share(sum(d <= 0.05 for d in diffs), len(diffs)),
            "spearman": round(cs.spearman([r["model_ratio"] for r in with_ratio], [r["scr_code"] for r in with_ratio]), 3)
            if len(with_ratio) > 2 else None},
        "listed_references_vs_code": {"n": len(with_list), "identical_set": share(sum(a == b for a, b in sets), len(sets)),
                                      "mean_jaccard": round(st.mean(jacc), 3) if jacc else None},
        "reference_count_vs_model": {
            "n": len(with_n),
            "identical": share(sum(r["model_n_refs"] == r["n_refs_grobid"] for r in with_n), len(with_n)),
            "within_2": share(sum(abs(r["model_n_refs"] - r["n_refs_grobid"]) <= 2 for r in with_n), len(with_n))},
    }
    (HERE / "self_citation_check.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
