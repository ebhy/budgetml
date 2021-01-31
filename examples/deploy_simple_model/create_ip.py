from budgetml import BudgetML

budgetml = BudgetML(project='PROJECT')

IP_ADDRESS = budgetml.create_static_ip('static-ip')
print(IP_ADDRESS)
