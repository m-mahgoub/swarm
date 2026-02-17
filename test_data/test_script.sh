# Test 1: See which compute node Slurm assigned to this task
echo "Task $SLURM_ARRAY_TASK_ID is running on $(hostname)"

# Test 2: Print the exact time to ensure jobs run simultaneously 
date

# Test 3: Sleep for a few seconds to simulate actual work, then print uptime
sleep 5 && uptime
