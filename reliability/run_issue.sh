#!/usr/bin/env bash
# Re-run the RUIN analysis of one ROMJIST issue with the published instructions.
#
#   reliability/run_issue.sh BATCH_ID OUTPUT_DIR [MODEL]
#
# Environment: CORPUS (downloaded PDFs, one folder per issue) and TEXT (output of
# extract_text.py) must be set. MODEL defaults to claude-opus-5-5.
#
# The published runs were executed as Claude Code subagents launched from an
# interactive session, each given exactly the prompt built below (with the
# authors' Windows paths). This script issues the same prompt through the
# Claude Code CLI in non-interactive mode. It was not itself used for the
# published runs; the prompt text is the part that must not change.
set -euo pipefail
BATCH="$1"; OUT="$2"; MODEL="${3:-claude-opus-5-5}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
: "${CORPUS:?set CORPUS to the downloaded corpus folder}"
: "${TEXT:?set TEXT to the extracted-text folder}"
FILES="$(awk -F, -v b="$BATCH" 'NR>1 && $1==b {sub(/^[^,]*,/, ""); gsub(/"/, ""); gsub(/,/, ", "); print}' "$REPO/reliability/batches.csv")"
[ -n "$FILES" ] || { echo "unknown batch $BATCH" >&2; exit 1; }
mkdir -p "$OUT"
# RUN_INSTRUCTIONS.md names the four specification files by the authors' checkout
# path; point the agent at this checkout instead.
python3 - "$REPO" "$OUT/.RUN_INSTRUCTIONS.local.md" <<'PY'
import sys
repo, out = sys.argv[1], sys.argv[2]
text = open(repo + "/reliability/RUN_INSTRUCTIONS.md", encoding="utf-8").read()
text = text.replace("D:\\Repositories\\ruin_framework", repo).replace(repo + "\\", repo + "/")
for part in ("framework", "journal-analysis", "data", "reliability"):
    text = text.replace(part + "\\", part + "/")
open(out, "w", encoding="utf-8").write(text)
PY
PROMPT="Read $OUT/.RUN_INSTRUCTIONS.local.md and follow the instructions below its \`---\` line exactly, with these values:

- TEXT_DIR = $TEXT/$BATCH (each paper's text file has the PDF's name with .txt in place of .pdf)
- BATCH_DIR = $CORPUS/$BATCH
- FILES = $FILES
- OUTPUT_FILE = $OUT/$BATCH.json
- TODAY = $(date +%F)"
claude -p "$PROMPT" --model "$MODEL" --allowedTools "Read,Write,Bash"
