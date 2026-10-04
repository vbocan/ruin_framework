# Environment for every scripted step of the ROMJIST_2026-10-04 run.
#
# Text extraction is the one step whose output depends on a tool version: the
# text SHA-256 values in pdf_manifest.csv were produced with poppler 25.03.0,
# which is what Debian trixie ships. A different poppler can produce different
# text from the same PDF, so use this image to compare text hashes.
#
#   docker build -t ruin-repro reliability/
#   docker run --rm -v "$PWD:/repo" -v /path/to/ROMJIST_corpus:/corpus:ro -w /repo ruin-repro \
#       python reliability/extract_text.py --corpus /corpus --text /tmp/text
FROM python:3.12-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && apt-get clean
RUN pip install --no-cache-dir "numpy>=1.24" "scipy>=1.10" "matplotlib>=3.7" "pandas>=2.0" "openpyxl>=3.1"
