import os
from budgetml import BudgetML
from predictor import Predictor

DOMAIN = os.getenv('DOMAIN', 'domain.com')
SUBDOMAIN = os.getenv('SUBDOMAIN', 'model')
IP_ADDRESS = os.getenv('IP_ADDRESS', '0.0.0.0')
GCP_MACHINE_TYPE = os.getenv('GCP_MACHINE_TYPE', 'e2-highmem-2')
GCP_PROJECT = os.getenv('GCP_PROJECT', 'budgetml')

budgetml = BudgetML(project=GCP_PROJECT)

out = budgetml.launch(
    Predictor,
    machine_type=GCP_MACHINE_TYPE,
    domain=DOMAIN,
    subdomain=SUBDOMAIN,
    requirements=['tensorflow==2.3.0', 'transformers'],
    static_ip=IP_ADDRESS
)
print(f"Credentials: {out}")