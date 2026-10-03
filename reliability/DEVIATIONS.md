# Deviations from PROTOCOL.md

## 1. Input is pre-extracted text, not PDF (2026-10-04, before the corpus run)

The protocol had each agent read the PDFs with the Read tool. The two-issue pilot
(2010 v13 n1, 2024 v27 n1) showed this does not give a fixed input: the Read
tool cannot render PDFs on the analysis machine (poppler's `pdftoppm` is
absent), so one agent fell back to running `pdftotext` itself, while the other
read the PDFs directly at more than twice the token cost. Two runs reading
different representations of the same paper would confound test–retest
variation with input variation.

Every PDF is therefore converted once, by `reliability/extract_text.py`, with
`pdftotext -enc UTF-8 -layout` (poppler 25.03.0), and every agent in every run
reads those text files. The text SHA-256 is recorded beside the PDF SHA-256 in
`pdf_manifest.csv`. `RUN_INSTRUCTIONS.md` is amended accordingly; nothing else
in it changes. The two pilot outputs are kept in `reliability/pilot/` for the
record and enter no result; both issues are re-run under the amended
instructions.

Formal notation survives text extraction imperfectly (two-dimensional layout
and some symbols are lost), which bears on the formalism judgments. This is a
limitation of the run, not a difference between runs.

## 2. Files that are not papers

Two of the 423 downloaded files are HTTP error pages saved under a `.pdf` name
(`2010-v13-n3/dcvoinescu.pdf`, 243 bytes; `2015-v18-n1/07-iperezhurtado_001.pdf`,
249 bytes): the journal's links for them are dead. They are not analysed.
`2011-v14-n4/07-ionascu.pdf` is a genuine PDF (7.5 MB) of scanned page images
with no text layer; it is passed to the agent like any other file and is
expected to be recorded as `PDF_CORRUPTED`. With `paper786.pdf` (2025 v28 n1)
unavailable at the publisher, 421 files are analysed.
