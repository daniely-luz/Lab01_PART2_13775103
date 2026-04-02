import os
import sys
import kagglehub
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from db import get_engine

path = kagglehub.dataset_download("sharmajicoder/college-students-habits-and-performance")
print("Downloaded to:", path)

csv_file = os.path.join(path, os.listdir(path)[0])
df = pd.read_csv(csv_file)
print(f"Loaded {len(df)} rows")

engine = get_engine()
df.to_sql("students", engine, if_exists="replace", index=False)
print("Raw layer: data inserted into 'students' table.")
