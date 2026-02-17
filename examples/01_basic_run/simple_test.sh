# Test 1: Identify the compute node
echo "Task $SLURM_ARRAY_TASK_ID is running on $(hostname)"

# Test 2: Print the current date and time
date

# Test 3: Simulate a brief workload
sleep 10 && echo "Task $SLURM_ARRAY_TASK_ID completed."
