"""Extract every research paper's reference list with GROBID.

The self-citation ratio that RUIN's flags rest on is counted by the model while
it reads the paper. This script gives an independent, deterministic count: GROBID
(0.8.2, CRF models, run as `docker run -d --name grobid -p 8070:8070
-e JAVA_TOOL_OPTIONS="-XX:-UseContainerSupport" lfoppiano/grobid:0.8.2`) parses
each PDF's reference list, and `../self_citation_check.py` matches the references
against the paper's own authors.

    python citations/references/extract_references.py --corpus D:/ROMJIST_corpus \
        --run journal-analysis/ROMJIST_2026-10-04

Writes citations/references/<batch_id>.json: for each research paper (by PDF
file name), the parsed references in order, each with its authors (forename,
surname), title, year, and the raw reference string. Standard library only.
"""

import argparse
import json
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEI = {"t": "http://www.tei-c.org/ns/1.0"}
GROBID = "http://localhost:8070/api/processReferences"


def post_pdf(pdf: Path) -> str:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (("consolidateCitations", "0"), ("includeRawCitations", "1")):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="input"; filename="{pdf.name}"\r\n'
                 f"Content-Type: application/pdf\r\n\r\n".encode() + pdf.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(GROBID, data=b"".join(parts), method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))


def text_of(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def parse(tei: str) -> list[dict]:
    root = ET.fromstring(tei)
    refs = []
    for bibl in root.iter(f"{{{TEI['t']}}}biblStruct"):
        authors = []
        for pers in bibl.findall(".//t:author/t:persName", TEI):
            authors.append({"forename": " ".join(text_of(f) for f in pers.findall("t:forename", TEI)),
                            "surname": text_of(pers.find("t:surname", TEI))})
        title = (text_of(bibl.find(".//t:analytic/t:title", TEI)) or text_of(bibl.find(".//t:monogr/t:title", TEI)))
        date = bibl.find(".//t:imprint/t:date", TEI)
        raw = bibl.find("t:note[@type='raw_reference']", TEI)
        refs.append({"authors": authors, "title": title,
                     "year": date.get("when", "")[:4] if date is not None else "",
                     "raw": text_of(raw)})
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args()
    total = 0
    for path in sorted(args.run.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        target = HERE / f'{batch["batch_id"]}.json'
        done = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
        for p in batch["papers"]:
            flags = set(p.get("flags") or [])
            if flags & {"EDITORIAL", "PDF_CORRUPTED"}:
                continue
            name = p["paper"]["source_file"]
            if name in done:
                continue
            refs = parse(post_pdf(args.corpus / batch["batch_id"] / name))
            done[name] = refs
            total += 1
            print(f'{batch["batch_id"]}/{name}: {len(refs)} references', flush=True)
        target.write_text(json.dumps(done, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{total} papers parsed")


if __name__ == "__main__":
    main()
