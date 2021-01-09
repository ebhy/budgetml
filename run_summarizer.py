from budgetml import BudgetML
from examples.summarizer.predictor import Predictor

DOMAIN = 'you-tldr.com'
SUBDOMAIN = 'models'

budgetml = BudgetML(
    project='ebhy-youtube'
)

# IP_ADDRESS = budgetml.create_static_ip('ebhy-youtube-static-ip')
# Create an A record that maps SUBDOMAIN.DOMAIN to IP_ADDRESS

budgetml.launch(
    Predictor,
    machine_type='e2-highmem-2',
    domain=DOMAIN,
    subdomain=SUBDOMAIN,
    requirements_path='examples/summarizer/requirements.txt',
    static_ip='35.225.200.179'
)
