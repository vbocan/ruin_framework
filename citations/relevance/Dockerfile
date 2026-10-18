# CPU image for specter2_relevance.py; the model weights are fetched at build
# time so that the run itself needs no network.
#   docker build -t ruin-specter2 citations/relevance
#   docker run --rm -v "$PWD:/work" -w /work ruin-specter2 \
#       python citations/relevance/specter2_relevance.py --run journal-analysis/ROMJIST_2026-10-04
FROM python:3.12-slim
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir transformers==4.48.3
ENV HF_HOME=/opt/hf
RUN python -c "from transformers import AutoModel, AutoTokenizer; \
AutoTokenizer.from_pretrained('allenai/specter2_base'); AutoModel.from_pretrained('allenai/specter2_base')"
ENV HF_HUB_OFFLINE=1
