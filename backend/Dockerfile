# No apt-get / build-essential — avoids deb.debian.org failures and 20+ min GCC downloads.
# All deps install from pre-built PyPI wheels only.
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    HF_HOME=/app/.cache/huggingface \
    PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .
RUN mkdir -p /app/data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/health', timeout=5)" || exit 1

CMD ["uvicorn", "karena.main:app", "--host", "0.0.0.0", "--port", "8080"]
