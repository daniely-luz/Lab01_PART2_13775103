#!/bin/bash
set -e

echo "=== RAW LAYER ==="
uv run python data/raw/ingestion_raw.py
uv run python data/raw/validate_raw.py

echo "=== SILVER LAYER ==="
uv run python data/silver/ingestion_silver.py
uv run python data/silver/report_silver.py
uv run python data/silver/chart_silver.py

echo "=== GOLD LAYER ==="
uv run python data/gold/ingestion_gold.py
uv run python data/gold/report_gold.py

echo "=== Pipeline concluído ==="
