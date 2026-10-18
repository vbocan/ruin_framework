# Source PDF for the worked example

The worked example analyses one paper, `paper708.pdf` (ROMJIST 2022, Volume 25,
Issue 1). The journal's PDFs are the publisher's content and are not
redistributed here. Download the file into this folder before running the
sample batch:

```bash
curl -o samples/input/papers/paper708.pdf https://romjist.ro/full-texts/paper708.pdf
```

Check that you hold the file the analysis read:

```bash
sha256sum samples/input/papers/paper708.pdf
# 8f14dae66da8c80ea35d2ad7891e9f0cfeb518f7877bf23dbd00020c8f94f6ba
```

The same hash is recorded in `reliability/pdf_manifest.csv`.
