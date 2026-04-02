import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(__file__)
CHARTS_DIR = os.path.join(BASE, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

df = pd.read_parquet(os.path.join(BASE, "students_silver.parquet"))

# 1. GPA Distribution
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(df["gpa"], bins=40, color="#4C72B0", edgecolor="white")
ax.axvline(df["gpa"].mean(), color="red", linestyle="--", label=f"Média: {df['gpa'].mean():.2f}")
ax.set_title("Distribuição do GPA")
ax.set_xlabel("GPA")
ax.set_ylabel("Contagem")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "01_gpa_distribution.png"), dpi=120)
plt.close(fig)

# 2. Performance Level
fig, ax = plt.subplots(figsize=(7, 5))
counts = df["performance_level"].value_counts()
bars = ax.bar(counts.index, counts.values, color=["#55A868", "#C44E52", "#8172B2"])
ax.bar_label(bars, fmt="%d")
ax.set_title("Alunos por Nível de Performance")
ax.set_xlabel("Nível")
ax.set_ylabel("Contagem")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "02_performance_level.png"), dpi=120)
plt.close(fig)

# 3. Study Hours vs GPA
sample = df.sample(min(3000, len(df)), random_state=42)
colors = {"Low": "#C44E52", "Medium": "#DD8452", "High": "#55A868"}
fig, ax = plt.subplots(figsize=(8, 5))
for level, group in sample.groupby("performance_level"):
    ax.scatter(group["study_hours"], group["gpa"], alpha=0.4, s=10,
               label=level, color=colors.get(level, "gray"))
ax.set_title("Horas de Estudo vs GPA")
ax.set_xlabel("Horas de Estudo")
ax.set_ylabel("GPA")
ax.legend(title="Performance")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "03_study_hours_vs_gpa.png"), dpi=120)
plt.close(fig)

# 4. Stress vs GPA
fig, ax = plt.subplots(figsize=(8, 5))
for level, group in sample.groupby("performance_level"):
    ax.scatter(group["stress"], group["gpa"], alpha=0.4, s=10,
               label=level, color=colors.get(level, "gray"))
ax.set_title("Estresse vs GPA")
ax.set_xlabel("Estresse")
ax.set_ylabel("GPA")
ax.legend(title="Performance")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "04_stress_vs_gpa.png"), dpi=120)
plt.close(fig)

# 5. Correlation Heatmap
key_cols = ["gpa", "study_hours", "attendance", "stress", "sleep_hours",
            "motivation", "procrastination_score", "final_score", "social_media_hours", "screen_time"]
corr = df[key_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
fig.colorbar(im, ax=ax)
ax.set_xticks(range(len(key_cols)))
ax.set_yticks(range(len(key_cols)))
ax.set_xticklabels(key_cols, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(key_cols, fontsize=8)
for i in range(len(key_cols)):
    for j in range(len(key_cols)):
        ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6)
ax.set_title("Mapa de Correlação — Features Principais")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "05_correlation_heatmap.png"), dpi=120)
plt.close(fig)

print("Gráficos salvos em:", CHARTS_DIR)

md = """# Camada Silver — Gráficos de Análise

## 1. Distribuição do GPA
![GPA Distribution](charts/01_gpa_distribution.png)

---

## 2. Alunos por Nível de Performance
![Performance Level](charts/02_performance_level.png)

---

## 3. Horas de Estudo vs GPA
![Study Hours vs GPA](charts/03_study_hours_vs_gpa.png)

---

## 4. Estresse vs GPA
![Stress vs GPA](charts/04_stress_vs_gpa.png)

---

## 5. Mapa de Correlação
![Correlation Heatmap](charts/05_correlation_heatmap.png)
"""

with open(os.path.join(BASE, "analysis_silver.md"), "w") as f:
    f.write(md)

print("Markdown salvo →", os.path.join(BASE, "analysis_silver.md"))
