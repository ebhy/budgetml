from budgetml import BudgetML
from predictor import MyPredictor

budgetml = BudgetML(
    project='budgetml'
)

budgetml.launch(MyPredictor)
