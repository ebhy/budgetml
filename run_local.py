from budgetml import BudgetML
from examples.fastsrgan.predictor import FastSRGANPredictor

budgetml = BudgetML(
    project='budgetml'
)

budgetml.launch_local(
    FastSRGANPredictor,
    requirements_path='examples/fastsrgan/requirements.txt',
)
