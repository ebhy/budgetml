from budgetml import BudgetML
from fastsrgan_predictor import FastSRGANPredictor

DOMAIN = 'pichance.com'
SUBDOMAIN = 'model'

budgetml = BudgetML(
    project='budgetml'
)

# IP_ADDRESS = budgetml.create_static_ip('pichance_static_ip')
# Create an A record that maps SUBDOMAIN.DOMAIN to IP_ADDRESS

budgetml.launch(
    FastSRGANPredictor,
    machine_type='e2-highmem-2',
    domain=DOMAIN,
    subdomain=SUBDOMAIN,
    requirements_path='/home/hamza/workspace/personal/budgetml'
                      '/fastsrgan_requirements.txt',
    static_ip='35.224.253.145'
)
