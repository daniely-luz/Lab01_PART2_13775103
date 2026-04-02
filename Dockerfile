FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen --no-dev

COPY db.py ./
COPY data/ ./data/
COPY entrypoint.sh ./
COPY .env.example .env

ENV PYTHONUNBUFFERED=1

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
