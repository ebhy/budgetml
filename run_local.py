from budgetml import BudgetML
from examples.summarizer.predictor import Predictor

budgetml = BudgetML(
    project='ebhy-youtube'
)

budgetml.launch_local(
    Predictor,
    requirements_path='examples/summarizer/requirements.txt',
)
