from budgetml import BudgetML
from examples.fastsrgan.predictor import FastSRGANPredictor

DOMAIN = 'pichance.com'
SUBDOMAIN = 'model'

budgetml = BudgetML(
    project='saas-generator'
)

# IP_ADDRESS = budgetml.create_static_ip('pichance-static-ip')
# Create an A record that maps SUBDOMAIN.DOMAIN to IP_ADDRESS

budgetml.launch(
    FastSRGANPredictor,
    machine_type='e2-highmem-2',
    domain=DOMAIN,
    subdomain=SUBDOMAIN,
    requirements_path='examples/fastsrgan/requirements.txt',
    static_ip='34.67.112.192'
)
