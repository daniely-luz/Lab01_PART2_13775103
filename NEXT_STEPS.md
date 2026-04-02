# Contexto para o próximo Claude

## O que é este projeto
Lab01 PART2 — replicação do Lab01 PART1 (medallion_project) com duas adições:
1. **UV** como gerenciador de dependências (já configurado: `pyproject.toml` + `uv.lock`)
2. **Docker** para subir PostgreSQL e rodar o pipeline em containers

## O que já foi feito
- Estrutura de pastas replicada do Part1:
  ```
  data/raw/ingestion_raw.py
  data/silver/ingestion_silver.py
  data/silver/report_silver.py
  data/silver/chart_silver.py
  data/silver/analysis_silver.md
  data/gold/ingestion_gold.py
  data/gold/report_gold.py
  ```
- `pyproject.toml` + `uv.lock` criados com UV
- `Dockerfile` criado
- `docker-compose.yml` criado
- `.gitignore` configurado (exclui `.venv`, `.env`, `*.parquet`, `*.txt`, `data/silver/charts/`)
- `.env.example` com `KAGGLE_API_TOKEN=your_kaggle_token_here`
- Repositório público criado: https://github.com/daniely-luz/Lab01_PART2_13775103

## O que FALTA fazer

### 1. Criar o .env com o token do Kaggle
```bash
cp .env.example .env
```
Editar `.env` e colocar o token real do Kaggle (o usuário tem o token, não subi no repo).

### 2. Verificar o docker-compose.yml e Dockerfile
Abrir os dois arquivos e confirmar:
- O `docker-compose.yml` deve ter dois serviços: `postgres` e `pipeline`
- Devem estar na mesma rede (`medallion-network`)
- A variável `DB_HOST` no pipeline deve apontar para o nome do serviço `postgres` (não `localhost`)
- Os scripts Python usam `localhost` hardcoded — precisam ser atualizados para ler `DB_HOST` de variável de ambiente

### 3. Atualizar os scripts para usar variável de ambiente DB_HOST
Os arquivos abaixo têm `host="localhost"` hardcoded na conexão SQLAlchemy:
- `data/raw/ingestion_raw.py`
- `data/silver/ingestion_silver.py`
- `data/gold/ingestion_gold.py`
- `data/gold/report_gold.py`

Devem ser atualizados para:
```python
import os
host = os.getenv("DB_HOST", "localhost")
```

### 4. Criar o banco `students` no container PostgreSQL
O banco precisa existir antes de rodar o pipeline. Pode ser feito via:
- Variável `POSTGRES_DB=students` no `docker-compose.yml` (serviço postgres)

### 5. Subir os containers
```bash
docker compose up --build
```

### 6. Ordem de execução dentro do container (ou localmente com uv)
```bash
# Localmente:
uv run python data/raw/ingestion_raw.py
uv run python data/silver/ingestion_silver.py
uv run python data/silver/report_silver.py
uv run python data/silver/chart_silver.py
uv run python data/gold/ingestion_gold.py
uv run python data/gold/report_gold.py
```

### 7. Commitar e fazer push das alterações finais
```bash
git add .
git commit -m "Adiciona Docker e corrige conexão via variável de ambiente"
git push
```

## Informações do banco de dados (ambiente local do usuário)
- Host: localhost
- Port: 5432
- Username: daniely.santos
- Password: (vazio)
- Database: students

## Dataset
- Fonte: https://www.kaggle.com/datasets/sharmajicoder/college-students-habits-and-performance
- 1.000.000 linhas, 42 colunas, dados sintéticos
- Baixado via `kagglehub` com `KAGGLE_API_TOKEN`
