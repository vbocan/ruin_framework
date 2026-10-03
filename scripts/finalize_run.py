"""Normalise a fresh run's batch files before scoring.

Analysing agents supply judgments; the bookkeeping around them is done here, the
same way for every batch, so that no agent's formatting choice reaches a table:

  * ``source`` is rebuilt from the corpus ``source.json`` for the issue. Agents
    set ``issue`` to null for labels such as "3-4" or "S", which the schema
    typed as a number; the label is kept as a string, as in the 2025 run.
  * ``paper_id`` is made unique across the whole run. An agent sees one issue,
    so two issues can both produce, say, ``popescu2024``; later occurrences, in
    batch order, get the next free letter suffix.

Run ``rescore.py --write`` afterwards to compute the derived fields.

    python scripts/finalize_run.py --input journal-analysis/ROMJIST_2026-10-04 \\
        --corpus /path/to/ROMJIST_corpus
"""

from __future__ import annotations

import argparse
import json
import string
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    args = ap.parse_args()

    seen: set[str] = set()
    renamed = fixed = 0
    for path in sorted(args.input.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        src = json.loads((args.corpus / batch["batch_id"] / "source.json").read_text(encoding="utf-8"))
        j, b = src["journal"], src["batch"]
        issue = b.get("issue", b.get("issue_label"))
        new_source = {"journal_acronym": j["acronym"], "journal_name": j["name"],
                      "journal_issn": j["issn"], "volume": b["volume"], "issue": issue,
                      "year": b["year"]}
        if batch.get("source") != new_source:
            batch["source"] = new_source
            fixed += 1
        for p in batch["papers"]:
            pid = p["paper_id"]
            if pid in seen:
                base = pid.rstrip(string.ascii_lowercase) if pid[-1:].isalpha() and pid[-2:-1].isdigit() else pid
                for suffix in string.ascii_lowercase:
                    if base + suffix not in seen:
                        p["paper_id"] = base + suffix
                        renamed += 1
                        break
            seen.add(p["paper_id"])
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(batch, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    print(f"source rebuilt in {fixed} batches; {renamed} paper_ids made unique; {len(seen)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
