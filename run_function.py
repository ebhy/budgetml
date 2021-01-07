from budgetml import BudgetML
import time
from budgetml.gcp.storage import upload_blob, create_bucket_if_not_exists

budgetml = BudgetML(
    project='budgetml'
)

unique_id = 'fast_test'
bucket_name = f'budget_bucket_{unique_id}'
create_bucket_if_not_exists(bucket_name)
# budgetml.create_cloud_function(unique_id, bucket_name)
upload_blob(bucket_name, 'run_function.py', 'test.py')