# Hugging Face Spaces — KarenaAI Backend
# Port 7860 (HF default)
FROM python:3.11-slim

WORKDIR /app

# System dependencies (no Tesseract — use pypdf text extraction only)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create required directories
RUN mkdir -p /tmp/data

# HF Spaces environment
ENV PORT=7860
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production
ENV DATABASE_URL=sqlite+aiosqlite:////tmp/karena.db
ENV AUDIT_DB_PATH=/tmp/audit.db

EXPOSE 7860

CMD ["python", "run.py"]
