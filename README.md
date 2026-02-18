# Swarm

## What is Swarm?

Swarm is a command-line tool that takes a single text file containing multiple bash commands and automatically converts them into a Slurm job array.

## What it does

Instead of manually writing complex Slurm array scripts and managing task IDs, you simply provide a list of commands you want to run. Swarm automatically splits them up, builds the required orchestration script, and submits them to the cluster for you.

## Supported Environments

Swarm is built to interact with the following cluster components:

- **Slurm Workload Manager:** For core job scheduling and array execution.
- **Environment Modules (Optional):** Supports loading cluster-native software via `module load` before your command runs.
- **Pyxis / Enroot (Optional):** Supports running tasks directly inside container images.

This tool is specifically designed and tested for the [Washington University RIS Scientific Compute Platform (Compute 2)](https://ris.wustl.edu/systems/scientific-compute-platform/).

_(Acknowledgments: This project is inspired by the [NIH Biowulf Swarm utility](https://github.com/NIH-HPC/swarm).)_

---

## Installation

Swarm is installed using `pip`. You can do this directly from GitHub, or by downloading the repository.

**Option 1: Install directly from GitHub**

```bash
# Upgrade pip
pip install --upgrade pip

# Install Swarm directly from the GitHub repository
pip install git+https://github.com/m-mahgoub/swarm.git
```

**Option 2: Download the repository and install**

```bash
# Clone the repository to your local cluster directory
git clone https://github.com/m-mahgoub/swarm.git

# Enter the directory
cd swarm

# Upgrade pip
pip install --upgrade pip

# Install the tool
pip install .

```

_(Note: Ensure your local `~/.local/bin` is in your system's PATH to run the command globally)._

---

## Expected Input File

Swarm expects a standard bash file (`.sh` or `.txt`).

- Each new line is treated as an independent task in the job array.
- Blank lines and comments (`#`) are ignored.
- Multi-line commands using a backslash (`\`) are correctly parsed as a single task.

**Example `commands.sh`:**

```bash
# Task 1
echo "Running task 1 on node $(hostname)"

# Task 2
python my_script.py --input data1.csv

# Task 3 (Multi-line command)
samtools view -bS input.sam \
  | samtools sort -o output.bam

```

---

## Command Line Options

Usage: `swarm [OPTIONS]`

| Option             | Shortcut | Description                                              | Default          |
| ------------------ | -------- | -------------------------------------------------------- | ---------------- |
| `--file`           | `-f`     | **[Required]** Input bash file with multiple commands.   |                  |
| `--chdir`          | `-D`     | Execution directory for the Slurm job.                   | File's directory |
| `--array_dir`      |          | Where to save the generated array scripts.               | `sbatch_arrays`  |
| `--partition`      | `-p`     | Partition to submit the job.                             | `general-cpu`    |
| `--output_log`     | `-o`     | Path to the output log file.                             | `%A_%a.log`      |
| `--error_log`      | `-e`     | Path to the error log file.                              | `%A_%a.err`      |
| `--time`           | `-t`     | Wall-clock time for job (e.g., 24:00:00).                | `24:00:00`       |
| `--cpus`           | `-c`     | Number of CPUs per task.                                 | `4`              |
| `--mem`            |          | Memory requirement per task (e.g., 8G).                  | `8G`             |
| `--sbatch_options` |          | Additional sbatch options (e.g., `--gres=gpu:1`).        |                  |
| `--job_name`       | `-J`     | Job name for the job array.                              | `swarm_array`    |
| `--rate_limit`     |          | Job submission rate limit (max simultaneous tasks).      |                  |
| `--image`          |          | Path or URL to the Pyxis/Enroot container image.         |                  |
| `--mounts`         |          | Comma-separated list of container mounts (`/src:/dest`). |                  |
| `--modules`        | `-m`     | Comma-separated list of modules to load.                 |                  |
| `--dry-run`        |          | Print the planned actions without executing them.        |                  |
| `--debug`          |          | Enable detailed debug logging to the terminal.           |                  |
| `--help`           |          | Show this message and exit.                              |                  |

---

## Usage Examples

Below are examples showing how to use Swarm.

### 1. Basic Usage (Minimal Command)

Run a basic bash file.

```bash
swarm -f examples/01_basic_run/simple_test.sh

```

### 2. Basic Usage (Dry Run)

Prints exactly what Swarm _would_ do and generates the scripts, but prevents actual submission to Slurm. Highly recommended before running large arrays.

```bash
swarm -f examples/01_basic_run/simple_test.sh --dry-run

```

### 3. Basic Usage (With Additional Options)

Overrides default resources to request 1 CPU, 16GB of memory, a 5-minute time limit, and a maximum of 10 tasks running simultaneously.

```bash
swarm -f examples/01_basic_run/simple_test.sh -c 1 --mem 16G -t 00:05:00 --rate_limit 10

```

### 4. Adding Extra Slurm Options

If you need to pass specific Slurm arguments that are not built into the Swarm CLI (like requesting a GPU or setting email alerts), you can pass them as a single string using `--sbatch_options`.

```bash
swarm -f examples/01_basic_run/simple_test.sh --partition=general-gpu --sbatch_options="--gres=gpu:1 --mail-type=ALL --mail-user=<YOUR_EMAIL@DOMAIN.COM>"

```

### 5. Using Cluster Modules

If your commands require software installed on the cluster, use the `--modules` flag. Swarm verifies these modules exist _before_ submitting the job to prevent instant failures. The modules will be loaded right before your command executes.

```bash
swarm -f examples/02_modules_image_run/test_with_modules_image.sh --partition=general-cpu --time=00:05:00 --modules samtools

```

### 6. Using Container Images (Pyxis/Enroot)

If your cluster supports Pyxis, you can run your tasks entirely inside a container (like a Docker image). The `--mounts` option is typically required so the container can see your local files.

**Setup: Mount the current directory so the container can access your data**

```bash
MOUNT_PATH="${PWD}"

```

**Using a DockerHub Image (Default format):**

```bash
swarm -f examples/02_modules_image_run/test_with_modules_image.sh --partition=general-cpu --time=00:05:00 --image biocontainers/samtools:v1.9-4-deb_cv1 --mounts "${MOUNT_PATH}:${MOUNT_PATH}"

```

**Using an Alternative Registry (e.g., Quay.io):**

**Format:** `[USER@][REGISTRY#]IMAGE[:TAG]|PATH`

```bash
swarm -f examples/02_modules_image_run/test_with_modules_image.sh --partition=general-cpu --time=00:05:00 --image quay.io#biocontainers/samtools:1.23--h96c455f_0 --mounts "${MOUNT_PATH}:${MOUNT_PATH}"

```
