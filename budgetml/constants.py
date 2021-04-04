import os

__version__ = '0.1.1'

APP_NAME = 'budgetml'
BUDGET_NGINX_PATH = os.getenv('BUDGET_NGINX_PATH', './nginx.conf')
BUDGET_CERTS_PATH = os.getenv('BUDGET_CERTS_PATH', './certs/')

BUDGETML_REGISTRY = 'us.gcr.io/budgetml'
BUDGETML_BASE_IMAGE_NAME = f'{BUDGETML_REGISTRY}/budgetml:base-{__version__}'