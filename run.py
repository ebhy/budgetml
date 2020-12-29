from budgetml import BudgetML
from fastsrgan_predictor import FastSRGANPredictor

budgetml = BudgetML(
    project='budgetml'
)

budgetml.launch(
    FastSRGANPredictor,
    domain='pichance.com',
    subdomain='api',
    requirements_path='/home/hamza/workspace/personal/budgetml/fastsrgan_requirements.txt',
    static_ip='35.224.253.145'
)
