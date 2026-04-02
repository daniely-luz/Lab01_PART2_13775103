# Lab01 PART2 — Arquitetura Medallion: Hábitos e Desempenho de Estudantes

**Dataset:** [College Students Habits and Performance](https://www.kaggle.com/datasets/sharmajicoder/college-students-habits-and-performance)
**Linhas:** 1.000.000 | **Colunas:** 42 | **Fonte:** Kaggle (sintético)

---

## 1. Arquitetura

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   Kaggle    │────►│   Camada RAW     │────►│   Camada SILVER      │────►│   Camada GOLD        │
│  (Fonte)    │     │  PostgreSQL      │     │   Arquivo Parquet    │     │  PostgreSQL           │
│             │     │  tabela:students │     │  students_silver     │     │  Star Schema          │
└─────────────┘     └──────────────────┘     └──────────────────────┘     └──────────────────────┘
      │                     │                          │                            │
  kagglehub            ingestion_raw.py          ingestion_silver.py        ingestion_gold.py
  download             inserção bruta            limpeza + parquet          tabelas dim + fato
                            │
                     validate_raw.py
                     Great Expectations
```

**Stack:** Python 3.12 · UV · Docker · PostgreSQL · Great Expectations · Metabase

---

## 2. Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado e rodando
- Token de API do Kaggle ([como obter](https://www.kaggle.com/docs/api#authentication))

---

## 3. Configuração do ambiente

### 3.1 Clonar o repositório

```bash
git clone https://github.com/daniely-luz/Lab01_PART2_13775103
cd Lab01_PART2_13775103
```

### 3.2 Criar o arquivo `.env`

```bash
cp .env.example .env
```

Edite o `.env` e insira o token real do Kaggle:

```
KAGGLE_API_TOKEN=seu_token_aqui
```

---

## 4. Como construir a imagem Docker

```bash
docker compose build
```

Isso constrói a imagem do serviço `pipeline` com Python 3.12 e todas as dependências instaladas via UV.

---

## 5. Como subir os containers

### Subir tudo (pipeline + PostgreSQL + Metabase)

```bash
docker compose up
```

O `docker-compose.yml` define três serviços:

| Serviço | Descrição | Porta |
|---------|-----------|-------|
| `postgres` | Banco de dados PostgreSQL 16 | `5433` (host) |
| `pipeline` | Executa o pipeline medallion completo | — |
| `metabase` | Dashboard de visualização | `3000` |

O serviço `pipeline` aguarda o PostgreSQL estar saudável antes de executar. A ordem de execução é:

```
ingestion_raw.py → validate_raw.py → ingestion_silver.py →
report_silver.py → chart_silver.py → ingestion_gold.py → report_gold.py
```

### Subir apenas PostgreSQL e Metabase (sem rodar o pipeline)

```bash
docker compose up postgres metabase
```

Útil quando os dados já estão carregados e você quer apenas visualizar no Metabase.

---

## 6. Como executar as validações do Great Expectations

### Via Docker (integrado ao pipeline)

As validações rodam automaticamente após a ingestão raw quando você executa `docker compose up`.

### Localmente (com UV)

```bash
# Instalar dependências
uv sync

# Executar somente a validação
uv run python data/raw/validate_raw.py
```

O script:
1. Baixa o dataset do Kaggle
2. Cria o contexto GX conectado ao filesystem (`gx/`)
3. Executa a suite `students_raw_suite` com 15 expectativas de 5 tipos distintos:

| Tipo de Expectativa | O que valida |
|--------------------|-------------|
| `ExpectTableRowCountToBeBetween` | Dataset não está vazio (≥ 1 linha) |
| `ExpectColumnToExist` | Colunas-chave existem: `gpa`, `study_hours`, `attendance`, `performance_level`, `sleep_hours` |
| `ExpectColumnValuesToNotBeNull` | Sem nulos em `gpa`, `study_hours`, `attendance`, `performance_level` |
| `ExpectColumnValuesToBeBetween` | GPA (0–4), attendance (0–100), sleep_hours (0–24), study_hours (≥ 0) |
| `ExpectTableColumnCountToBeBetween` | Dataset contém entre 40 e 50 colunas |

4. Gera o relatório HTML (Data Docs) e abre automaticamente no browser

O relatório HTML fica salvo em:
```
gx/uncommitted/data_docs/local_site/index.html
```

Para abrir manualmente:
```bash
open gx/uncommitted/data_docs/local_site/index.html
```

---

## 7. Visualização com Metabase

Após subir os containers, acesse **http://localhost:3000**.

Na configuração inicial, conecte ao banco de dados com:

| Campo | Valor |
|-------|-------|
| Tipo | PostgreSQL |
| Host | `postgres` |
| Porta | `5432` |
| Banco | `students` |
| Usuário | `daniely.santos` |
| Senha | *(vazio)* |

---

## 8. Documentação dos Scripts

### `data/raw/ingestion_raw.py` — Camada Raw
Download do dataset via `kagglehub` e inserção bruta na tabela `students` do PostgreSQL.

### `data/raw/validate_raw.py` — Validação GX
Valida a qualidade dos dados brutos com Great Expectations e gera Data Docs HTML.

### `data/silver/ingestion_silver.py` — Camada Silver
Lê a tabela `students` e aplica:
- Padronização de nomes de colunas para `snake_case`
- Remoção de duplicatas
- Imputação de valores ausentes (mediana para numéricos, `"unknown"` para categóricos)
- Detecção automática de colunas de data
- Salva em `data/silver/students_silver.parquet`

### `data/silver/report_silver.py` — Relatório Silver
Gera `data/silver/students_silver_report.txt` com tipos, contagem de nulos e estatísticas descritivas.

### `data/silver/chart_silver.py` — Gráficos Silver
Gera 5 gráficos de análise em `data/silver/charts/`.

| Gráfico | Descrição |
|---------|-----------|
| Distribuição do GPA | Histograma com linha da média |
| Nível de Performance | Barras por nível (Low/Medium/High) |
| Horas de Estudo vs GPA | Scatter colorido por performance |
| Estresse vs GPA | Impacto do estresse no desempenho |
| Mapa de Correlação | Correlações de Pearson entre 10 features |

### `data/gold/ingestion_gold.py` — Camada Gold (Star Schema)
Lê o Parquet silver e carrega um Star Schema no PostgreSQL:

```
fact_student_performance
  ├── dim_performance   (nível de desempenho)
  ├── dim_student       (dados demográficos)
  ├── dim_lifestyle     (sono, estresse, tela, redes sociais...)
  └── dim_academic      (horas de estudo, frequência, procrastinação...)
```

### `data/gold/report_gold.py` — Perguntas de Negócio
5 queries SQL sobre o Star Schema. Resultados em `data/gold/business_report_gold.txt`.

---

## 9. Qualidade de Dados

| Problema | Detalhe | Resolução |
|----------|---------|-----------|
| **Valores ausentes** | 1.558 linhas com `performance_level = null` | Imputado como `"unknown"` |
| **Duplicatas** | Nenhuma em 1.000.000 linhas | — |
| **Nomes de colunas** | Mixed case com espaços | Padronizados para `snake_case` |
| **Escala do GPA** | Máx = 2.009 (não 0–10 como descrito) | Mantido; escala real é 0–2 |

> Os 1.558 registros `unknown` apresentam GPA médio 0.0, 48,6% de presença e procrastinação 7,56 — provavelmente alunos com pior rendimento que não preencheram o campo.

---

## 10. Perguntas de Negócio (Camada Gold)

**Q1 — GPA Médio por Nível de Performance**
Alunos de baixo desempenho têm GPA médio de 0,83 e nota final de 64,9.

**Q2 — Impacto do Estilo de Vida no GPA**
Maior estresse e menos sono correlacionam com piores resultados.

**Q3 — Hábitos Acadêmicos por Nível de Performance**
O grupo `unknown` estuda 0,42h/dia com 48,6% de presença e procrastinação 7,56.

**Q4 — Renda Familiar vs GPA**
Escolaridade dos pais é o fator mais forte: nível 0 → GPA 0,68; nível 5 → GPA 0,98.

**Q5 — Perfil Top 10% vs Bottom 10%**

| Métrica | Top 10% | Bottom 10% |
|---------|---------|------------|
| GPA Médio | 1,35 | 0,32 |
| Horas de estudo/dia | 7,33 | 1,11 |
| Presença | 93,2% | 56,3% |
| Procrastinação | 3,33 | 6,65 |
| Motivação | 7,09 | 4,89 |

---

## 11. Dicionário de Dados

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `study_hours` | float | Horas diárias dedicadas ao estudo |
| `attendance` | float | Percentual de presença (0–100) |
| `assignment_completion` | float | Percentual de tarefas concluídas (0–100) |
| `midterm_score` | float | Nota da prova intermediária (0–100) |
| `final_score` | float | Nota da prova final (0–100) |
| `project_score` | float | Nota do projeto (0–100) |
| `backlogs` | int | Matérias reprovadas/pendentes |
| `sleep_hours` | float | Média de horas de sono por noite |
| `stress` | float | Estresse autorrelatado (1–10) |
| `anxiety` | float | Pontuação de ansiedade (0–100) |
| `depression` | float | Pontuação de depressão (0–100) |
| `motivation` | float | Motivação (1–10) |
| `concentration` | float | Concentração (1–10) |
| `time_management` | float | Gestão do tempo (1–10) |
| `self_discipline` | float | Autodisciplina (1–10) |
| `social_media_hours` | float | Horas diárias em redes sociais |
| `gaming_hours` | float | Horas diárias jogando |
| `netflix_hours` | float | Horas diárias em streaming |
| `screen_time` | float | Tempo total diário de tela (horas) |
| `physical_activity` | float | Horas semanais de atividade física |
| `junk_food_frequency` | float | Consumo de junk food por semana |
| `caffeine_mg` | float | Consumo diário de cafeína em mg |
| `late_night_frequency` | float | Frequência semanal de madrugadas acordado |
| `procrastination_score` | float | Procrastinação (1–10) |
| `family_income` | float | Renda familiar anual |
| `parental_education_level` | int | Escolaridade dos pais (0=nenhum → 5=pós-graduação) |
| `internet_quality` | float | Qualidade da internet (1–10) |
| `library_visits` | float | Visitas à biblioteca por semana |
| `online_courses_completed` | int | Cursos online concluídos |
| `part_time_hours` | float | Horas semanais em trabalho part-time |
| `peer_study_group` | int | Participa de grupo de estudos (0/1) |
| `relationship_status` | int | Em relacionamento (0/1) |
| `hostel_student` | int | Mora em república/alojamento (0/1) |
| `extracurricular_hours` | float | Horas semanais em atividades extracurriculares |
| `phone_unlocks_per_day` | float | Desbloqueios do celular por dia |
| `previous_gpa` | float | GPA do semestre anterior |
| `class_participation` | float | Participação em sala (1–10) |
| `weekly_study_sessions` | float | Sessões de estudo por semana |
| `group_study_hours` | float | Horas semanais de estudo em grupo |
| `financial_stress` | float | Estresse financeiro (1–10) |
| `gpa` | float | GPA atual (0–2) |
| `performance_level` | str | Nível de desempenho (Low / Medium / High) |
