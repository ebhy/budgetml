from budgetml import BudgetML
from fastsrgan_predictor import FastSRGANPredictor

budgetml = BudgetML(
    project='budgetml'
)

budgetml.launch(
    FastSRGANPredictor,
    domain='pichance.com',
    subdomain='budget',
    requirements_path='/home/hamza/workspace/personal/budgetml/fastsrgan_requirements.txt'
)
