# Swarm Tool

## Description
Swarm is a command-line tool designed to simplify and manage batch job submissions on SLURM clusters. It provides an easy-to-use interface for running scripts, loading modules, and utilizing containerized environments, making it ideal for high-performance computing workflows.

---

## Installation
To install Swarm, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/m-mahgoub/swarm.git
   ```

2. Navigate to the project directory:
   ```bash
   cd swarm
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the tool:
   ```bash
   pip install .
   ```

---

## Command-Line Options
Swarm provides the following CLI options:

- `-f <file>`: Specify the script file to run.
- `--partition <partition>`: Define the SLURM partition to use.
- `--time <time>`: Set the maximum runtime for the job.
- `--modules <modules>`: Load specific modules before running the script.
- `--image <image>`: Use a container image for the job.
- `--mounts <mounts>`: Specify directories to mount in the container.
- `--dry-run`: Simulate the job submission without actually running it.

---

## Usage Examples
Here are some examples to verify that Swarm is working correctly:

### Example 1: Basic Script Execution
Run a simple test script:
```bash
swarm -f examples/01_basic_run/simple_test.sh --partition=general-cpu --time=00:05:00
```

### Example 2: Using Modules
Run a script with the `samtools` module loaded:
```bash
mkdir -p examples/02_modules_image_run
cat << 'EOF' > examples/02_modules_image_run/test_with_modules_image.sh
# Test 1
samtools --help

# Test 2
samtools --version
EOF

swarm -f examples/02_modules_image_run/test_with_modules_image.sh --partition=general-cpu --time=00:05:00 --modules samtools
```

### Example 3: Using a Container Image
Run a script with a containerized environment:
```bash
MOUNT_PATH="${PWD}"
swarm -f examples/02_modules_image_run/test_with_modules_image.sh \
  --partition=general-cpu \
  --time=00:05:00 \
  --image biocontainers/samtools:v1.9-4-deb_cv1 \
  --mounts "${MOUNT_PATH}:${MOUNT_PATH}"
```

---

For more details, refer to the `dev.sh` file or the project documentation.