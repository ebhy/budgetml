from budgetml import BudgetML
from examples.fastsrgan.predictor import FastSRGANPredictor

DOMAIN = 'pichance.com'
SUBDOMAIN = 'model'

budgetml = BudgetML(
    project='budgetml'
)

# IP_ADDRESS = budgetml.create_static_ip('pichance-static-ip')
# Create an A record that maps SUBDOMAIN.DOMAIN to IP_ADDRESS

budgetml.launch(
    FastSRGANPredictor,
    machine_type='e2-highmem-2',
    domain=DOMAIN,
    subdomain=SUBDOMAIN,
    requirements_path='examples/fastsrgan/fastsrgan_requirements.txt',
    static_ip='35.224.253.145'
)
