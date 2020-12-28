import os

BUDGET_NGINX_PATH = os.getenv('BUDGET_NGINX_PATH', './nginx.conf')
BUDGET_CERTS_PATH = os.getenv('BUDGET_CERTS_PATH', './certs/')