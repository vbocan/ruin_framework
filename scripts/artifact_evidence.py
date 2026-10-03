"""Extract artifact-availability evidence from the source PDFs.

The original corpus run scored artifact availability as a judged component,
and the provenance records show the judgment drifted from the anchors in
framework/scoring.md: papers that described an artifact without releasing it
were credited at 50-70, and 250 of the 415 provenance records say nothing about
artifacts at all, so the score cannot be audited from the archive alone.

This script makes the evidence auditable. For every research paper it locates
the source PDF, converts it to text with pdftotext (poppler), and records

    * every URL in the text, with its surrounding sentence and whether it sits
      in the reference list, and
    * every sentence that states, denies, or qualifies the availability of
      code, software, data, or supplementary material.

It performs no scoring. The evidence file it writes is the input to the
artifact re-assessment recorded in data/artifact_rescore.csv, whose categories
map to the five anchors through ruin_scoring.ARTIFACT_ANCHORS.

PDFs are matched to records by title, because the downloader keeps the
journal's own file names, which do not follow the dataset's paper_id scheme.

Usage
-----
    python scripts/artifact_evidence.py --corpus /path/to/ROMJIST_corpus \\
        --input journal-analysis/ROMJIST_29.12.2025 \\
        --output data/artifact_evidence.jsonl

Requires pdftotext on PATH (Debian: apt-get install poppler-utils).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ruin_scoring as rs  # noqa: E402

URL = re.compile(
    r"(?:https?://|ftp://|www\.)[^\s<>\"'\)\]]+"
    r"|\b(?:github|gitlab|bitbucket|sourceforge)\.(?:com|org|io)/[^\s<>\"'\)\]]+",
    re.I,
)

#: Hosts that only ever identify publications, never artifacts.
PUBLICATION_HOSTS = re.compile(r"doi\.org|dx\.doi|ieeexplore|springer|sciencedirect|"
                               r"acm\.org/doi|arxiv\.org/abs|scholar\.google|romjist\.ro", re.I)

#: Sentences about availability. Deliberately broad: the assessor reads every
#: hit, so a false positive costs a line of reading and a miss costs a score.
STATEMENT = re.compile(
    r"github|gitlab|bitbucket|zenodo|figshare|kaggle|sourceforge|code\.google|osf\.io|"
    r"huggingface|dataport|physionet|mendeley data|\buci\b|machine learning repository|"
    r"(?:source|our|the|matlab|python|java|c\+\+)?\s*(?:code|software|implementation|program|"
    r"tool|toolbox|simulator|scripts?)\b[^.]{0,80}\b(?:available|released|public|publicly|"
    r"download|repository|open[- ]source|free(?:ly)?|online|request|provided|shared|hosted)|"
    r"(?:data ?sets?|data|database|corpus|benchmark|recordings|measurements|images)\b[^.]{0,80}"
    r"\b(?:available|public|publicly|download|repository|obtained from|taken from|provided by|"
    r"collected|acquired|request|online)|"
    r"upon request|on request|supplementary (?:material|file|data)|data availability|"
    r"code availability|open[- ]source",
    re.I,
)

#: Sentences naming the data a paper's results rest on. A paper evaluated on a
#: public benchmark often says so without any availability vocabulary.
DATA_MENTION = re.compile(r"\b(?:data ?sets?|databases?|corpus|corpora|benchmarks?)\b", re.I)
MAX_DATA_MENTIONS = 15

REFERENCES_HEADING =re.compile(r"^\s*(?:\d+\.?\s*)?(references|bibliography)\s*$", re.I | re.M)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def pdftotext(pdf: Path, first_pages: int | None = None) -> str:
    cmd = ["pdftotext", "-enc", "UTF-8"]
    if first_pages:
        cmd += ["-l", str(first_pages)]
    cmd += [str(pdf), "-"]
    try:
        return subprocess.run(cmd, capture_output=True, check=True, timeout=120).stdout.decode(
            "utf-8", "replace")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def sentences(text: str) -> list[str]:
    text = re.sub(r"-\n(?=[a-z])", "", text)          # rejoin hyphenated line breaks
    text = re.sub(r"\s*\n\s*", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\[(])", text) if s.strip()]


def match_pdfs(papers: list[dict], pdfs: list[Path]) -> dict[str, tuple[Path, float]]:
    """Assign each paper the PDF whose opening text best contains its title."""
    heads = {pdf: norm(pdftotext(pdf, first_pages=2))[:4000] for pdf in pdfs}
    out: dict[str, tuple[Path, float]] = {}
    taken: set[Path] = set()
    scored = []
    for p in papers:
        title = norm((p.get("paper") or {}).get("title") or "")
        if not title:
            continue
        for pdf, head in heads.items():
            if title and title in head:
                score = 1.0
            else:
                sm = difflib.SequenceMatcher(None, title, head[: max(len(title) * 4, 400)])
                blk = sm.find_longest_match(0, len(title), 0, len(sm.b))
                score = blk.size / max(len(title), 1)
            scored.append((score, p["paper_id"], pdf))
    for score, pid, pdf in sorted(scored, key=lambda x: -x[0]):
        if pid in out or pdf in taken or score < 0.5:
            continue
        out[pid] = (pdf, round(score, 3))
        taken.add(pdf)
    # Fallback for titles the journal printed differently from its index (one
    # 2013 paper) or that pdftotext runs together ("SiO2Nanoparticles"): pair a
    # leftover paper with the leftover PDF of the same issue whose first page
    # carries the first author's surname. Recorded with title_match 0.0 so the
    # pairing is visibly not a title match.
    for p in papers:
        if p["paper_id"] in out:
            continue
        authors = (p.get("paper") or {}).get("authors") or []
        surname = norm(authors[0]).split()[-1] if authors else ""
        hits = [pdf for pdf, head in heads.items()
                if pdf not in taken and surname and surname in head.split()]
        if len(hits) == 1:
            out[p["paper_id"]] = (hits[0], 0.0)
            taken.add(hits[0])
    return out


def evidence(pdf: Path) -> dict:
    text = pdftotext(pdf)
    m = list(REFERENCES_HEADING.finditer(text))
    ref_start = m[-1].start() if m else len(text)
    body_sents = sentences(text[:ref_start])
    ref_sents = sentences(text[ref_start:])
    urls = []
    for where, sents in (("body", body_sents), ("references", ref_sents)):
        for s in sents:
            for u in URL.findall(s):
                u = u.rstrip(".,;:")
                if PUBLICATION_HOSTS.search(u):
                    continue
                urls.append({"url": u, "where": where, "context": s[:400]})
    statements = [s[:400] for s in body_sents if STATEMENT.search(s)]
    data_mentions = [s[:300] for s in body_sents
                     if DATA_MENTION.search(s) and not STATEMENT.search(s)][:MAX_DATA_MENTIONS]
    return {
        "chars": len(text),
        "urls": urls,
        "statements": statements,
        "data_mentions": data_mentions,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    n = unmatched = 0
    with args.output.open("w", encoding="utf-8") as out:
        for path in sorted(args.input.glob("*.json")):
            batch = json.loads(path.read_text(encoding="utf-8"))
            bid = batch["batch_id"]
            papers = [p for p in batch.get("papers", []) if rs.is_research(p.get("flags", []) or [])]
            pdfs = sorted((args.corpus / bid).glob("*.pdf"))
            matched = match_pdfs(papers, pdfs)
            for p in papers:
                pid = p["paper_id"]
                rec = {"paper_id": pid, "batch_id": bid,
                       "title": (p.get("paper") or {}).get("title")}
                if pid in matched:
                    pdf, score = matched[pid]
                    rec.update({"pdf": pdf.name, "title_match": score}, **evidence(pdf))
                else:
                    unmatched += 1
                    rec.update({"pdf": None, "title_match": 0.0, "chars": 0,
                                "urls": [], "statements": [], "data_mentions": []})
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
            print(f"{bid}: {len(papers)} papers, {len(pdfs)} PDFs, {len(matched)} matched")
    print(f"\n{n} records written to {args.output}; {unmatched} without a matched PDF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
