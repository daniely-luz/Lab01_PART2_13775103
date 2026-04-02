import os
import sys
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from db import get_engine

engine = get_engine()


def q1_avg_gpa_by_performance() -> pd.DataFrame:
    sql = """
        SELECT p.performance_level, COUNT(*) AS total_students,
               ROUND(AVG(f.gpa)::numeric, 2) AS avg_gpa,
               ROUND(AVG(f.final_score)::numeric, 2) AS avg_final_score,
               ROUND(AVG(f.midterm_score)::numeric, 2) AS avg_midterm_score
        FROM fact_student_performance f
        JOIN dim_performance p USING (performance_id)
        GROUP BY p.performance_level ORDER BY avg_gpa DESC
    """
    return pd.read_sql(text(sql), engine)


def q2_lifestyle_impact_on_gpa() -> pd.DataFrame:
    sql = """
        SELECT p.performance_level,
               ROUND(AVG(l.stress)::numeric, 2) AS avg_stress,
               ROUND(AVG(l.sleep_hours)::numeric, 2) AS avg_sleep_hours,
               ROUND(AVG(l.screen_time)::numeric, 2) AS avg_screen_time,
               ROUND(AVG(l.social_media_hours)::numeric, 2) AS avg_social_media_hours,
               ROUND(AVG(l.motivation)::numeric, 2) AS avg_motivation
        FROM fact_student_performance f
        JOIN dim_performance p USING (performance_id)
        JOIN dim_lifestyle l USING (lifestyle_id)
        GROUP BY p.performance_level ORDER BY avg_stress DESC
    """
    return pd.read_sql(text(sql), engine)


def q3_academic_habits_by_performance() -> pd.DataFrame:
    sql = """
        SELECT p.performance_level,
               ROUND(AVG(a.study_hours)::numeric, 2) AS avg_study_hours,
               ROUND(AVG(a.attendance)::numeric, 2) AS avg_attendance,
               ROUND(AVG(a.assignment_completion)::numeric, 2) AS avg_assignment_completion,
               ROUND(AVG(a.procrastination_score)::numeric, 2) AS avg_procrastination,
               ROUND(AVG(a.backlogs)::numeric, 2) AS avg_backlogs
        FROM fact_student_performance f
        JOIN dim_performance p USING (performance_id)
        JOIN dim_academic a USING (academic_id)
        GROUP BY p.performance_level ORDER BY avg_study_hours DESC
    """
    return pd.read_sql(text(sql), engine)


def q4_financial_background_vs_gpa() -> pd.DataFrame:
    sql = """
        WITH percentiles AS (
            SELECT PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY family_income) AS p33,
                   PERCENTILE_CONT(0.66) WITHIN GROUP (ORDER BY family_income) AS p66
            FROM dim_student
        )
        SELECT
            CASE WHEN s.family_income < pc.p33 THEN 'Baixa Renda'
                 WHEN s.family_income < pc.p66 THEN 'Média Renda'
                 ELSE 'Alta Renda' END AS faixa_renda,
            s.parental_education_level,
            ROUND(AVG(f.gpa)::numeric, 2) AS avg_gpa,
            ROUND(AVG(f.final_score)::numeric, 2) AS avg_final_score,
            COUNT(*) AS total_students
        FROM fact_student_performance f
        JOIN dim_student s USING (student_id)
        CROSS JOIN percentiles pc
        GROUP BY faixa_renda, s.parental_education_level
        ORDER BY faixa_renda, s.parental_education_level
    """
    return pd.read_sql(text(sql), engine)


def q5_top10_vs_bottom10() -> pd.DataFrame:
    sql = """
        WITH ranked AS (
            SELECT f.gpa, f.financial_stress, a.study_hours, a.attendance,
                   a.procrastination_score, l.stress, l.sleep_hours, l.motivation,
                   NTILE(10) OVER (ORDER BY f.gpa) AS decile
            FROM fact_student_performance f
            JOIN dim_academic a USING (academic_id)
            JOIN dim_lifestyle l USING (lifestyle_id)
        )
        SELECT
            CASE WHEN decile = 10 THEN 'Top 10%' ELSE 'Bottom 10%' END AS grupo,
            COUNT(*) AS alunos,
            ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
            ROUND(AVG(study_hours)::numeric, 2) AS avg_study_hours,
            ROUND(AVG(attendance)::numeric, 2) AS avg_attendance,
            ROUND(AVG(procrastination_score)::numeric, 2) AS avg_procrastination,
            ROUND(AVG(stress)::numeric, 2) AS avg_stress,
            ROUND(AVG(sleep_hours)::numeric, 2) AS avg_sleep,
            ROUND(AVG(motivation)::numeric, 2) AS avg_motivation
        FROM ranked WHERE decile IN (1, 10)
        GROUP BY grupo ORDER BY avg_gpa DESC
    """
    return pd.read_sql(text(sql), engine)


if __name__ == "__main__":
    questions = [
        ("Q1 — GPA Médio por Nível de Performance",          q1_avg_gpa_by_performance),
        ("Q2 — Impacto do Estilo de Vida no GPA",            q2_lifestyle_impact_on_gpa),
        ("Q3 — Hábitos Acadêmicos por Nível de Performance", q3_academic_habits_by_performance),
        ("Q4 — Renda Familiar vs GPA",                       q4_financial_background_vs_gpa),
        ("Q5 — Perfil Top 10% vs Bottom 10%",                q5_top10_vs_bottom10),
    ]

    lines = []
    lines.append("GOLD LAYER — RELATÓRIO DE PERGUNTAS DE NEGÓCIO\n")
    lines.append("=" * 60 + "\n\n")

    for title, fn in questions:
        lines.append("=" * 60 + "\n")
        lines.append(f"  {title}\n")
        lines.append("=" * 60 + "\n")
        result = fn()
        lines.append(result.to_string(index=False) + "\n\n")
        print(f"\n{'='*60}\n  {title}\n{'='*60}")
        print(result.to_string(index=False))

    report_path = os.path.join(os.path.dirname(__file__), "business_report_gold.txt")
    with open(report_path, "w") as f:
        f.writelines(lines)
    print(f"\nRelatório salvo → {report_path}")
