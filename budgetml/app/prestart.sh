# bash generate random 32 character alphanumeric string (upper and lowercase) and
export BUDGET_TOKEN=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)