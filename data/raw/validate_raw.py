import os
import re
import sys
import webbrowser

import kagglehub
import pandas as pd
import great_expectations as gx

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GX_DIR = ROOT  # GX cria subdiretório gx/ dentro do project_root_dir


def to_snake_case(name: str) -> str:
    name = re.sub(r"[\s\-]+", "_", name.strip())
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


# ── 1. Carregar dados ─────────────────────────────────────────────────────────
print("Baixando dataset...")
path = kagglehub.dataset_download("sharmajicoder/college-students-habits-and-performance")
csv_file = os.path.join(path, os.listdir(path)[0])
df = pd.read_csv(csv_file)
df.columns = [to_snake_case(c) for c in df.columns]
print(f"Dataset carregado: {len(df)} linhas, {len(df.columns)} colunas")
print(f"Colunas: {list(df.columns)}\n")

# ── 2. Contexto GX (filesystem) ───────────────────────────────────────────────
context = gx.get_context(mode="file", project_root_dir=GX_DIR)

# ── 3. Datasource Pandas ──────────────────────────────────────────────────────
DS_NAME = "students_raw_pandas"
ASSET_NAME = "students_df"
BATCH_NAME = "full_batch"

try:
    ds = context.data_sources.get(DS_NAME)
except Exception:
    ds = context.data_sources.add_pandas(DS_NAME)

try:
    asset = ds.get_asset(ASSET_NAME)
except Exception:
    asset = ds.add_dataframe_asset(ASSET_NAME)

try:
    batch_def = asset.get_batch_definition(BATCH_NAME)
except Exception:
    batch_def = asset.add_batch_definition_whole_dataframe(BATCH_NAME)

# ── 4. Suite de Expectativas ──────────────────────────────────────────────────
SUITE_NAME = "students_raw_suite"

try:
    context.suites.delete(SUITE_NAME)
except Exception:
    pass

suite = context.suites.add(gx.ExpectationSuite(name=SUITE_NAME))

expectations = [
    # 1. Volume mínimo de linhas
    gx.expectations.ExpectTableRowCountToBeBetween(min_value=1),

    # 2. Colunas-chave existem no dataset
    gx.expectations.ExpectColumnToExist(column="gpa"),
    gx.expectations.ExpectColumnToExist(column="study_hours"),
    gx.expectations.ExpectColumnToExist(column="attendance"),
    gx.expectations.ExpectColumnToExist(column="performance_level"),
    gx.expectations.ExpectColumnToExist(column="sleep_hours"),

    # 3. Valores não nulos em colunas críticas
    gx.expectations.ExpectColumnValuesToNotBeNull(column="gpa"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="study_hours"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="performance_level"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="attendance"),

    # 4. GPA entre 0 e 4
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="gpa", min_value=0.0, max_value=4.0
    ),

    # 5. Frequência (attendance) entre 0% e 100%
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="attendance", min_value=0.0, max_value=100.0
    ),

    # 6. Horas de sono entre 0 e 24
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="sleep_hours", min_value=0.0, max_value=24.0
    ),

    # 7. Horas de estudo >= 0
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="study_hours", min_value=0.0
    ),

    # 8. Quantidade de colunas compatível com o dataset (42 cols)
    gx.expectations.ExpectTableColumnCountToBeBetween(min_value=40, max_value=50),
]

for exp in expectations:
    suite.add_expectation(exp)

print(f"Suite '{SUITE_NAME}' criada com {len(suite.expectations)} expectativas.\n")

# ── 5. Validation Definition ──────────────────────────────────────────────────
VD_NAME = "students_raw_validation"

try:
    context.validation_definitions.delete(VD_NAME)
except Exception:
    pass

vd = context.validation_definitions.add(
    gx.ValidationDefinition(name=VD_NAME, data=batch_def, suite=suite)
)

# ── 6. Executar validação ─────────────────────────────────────────────────────
print("Executando validação...")
result = vd.run(batch_parameters={"dataframe": df})

passed = sum(1 for r in result.results if r.success)
total = len(result.results)
print(f"\n{'✓' if result.success else '✗'} Validação: {passed}/{total} expectativas passaram")

for r in result.results:
    status = "✓" if r.success else "✗"
    exp_type = r.expectation_config.type
    kwargs = {k: v for k, v in r.expectation_config.kwargs.items() if k != "batch_id"}
    print(f"  {status} {exp_type}({kwargs})")

# ── 7. Gerar Data Docs (HTML) ─────────────────────────────────────────────────
print("\nGerando Data Docs...")
context.build_data_docs()

docs_sites = context.get_docs_sites_urls()
if docs_sites:
    report_url = docs_sites[0]["site_url"]
    print(f"\nData Docs gerado em:\n  {report_url}")
    try:
        webbrowser.open(report_url)
        print("  (abrindo no browser...)")
    except Exception:
        pass
else:
    fallback = os.path.join(GX_DIR, "uncommitted", "data_docs", "local_site", "index.html")
    print(f"\nData Docs gerado em:\n  file://{os.path.abspath(fallback)}")
