FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen --no-dev

COPY data/ ./data/
COPY .env.example .env

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "data/raw/ingestion_raw.py"]
