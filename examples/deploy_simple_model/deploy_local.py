import os
from budgetml import BudgetML
from predictor import Predictor

GCP_PROJECT = os.getenv('GCP_PROJECT', 'budgetml')

budgetml = BudgetML(project=GCP_PROJECT)
out = budgetml.launch_local(
    Predictor,
    requirements=['tensorflow==2.3.0', 'transformers'],
)
print(f"Credentials: {out}")