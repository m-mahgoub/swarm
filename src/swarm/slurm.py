import logging
import subprocess
from pathlib import Path
from typing import List

# Set up our logger for debugging
logger = logging.getLogger(__name__)

def submit_job_array(
    job_scripts: List[Path],
    output_log: str,
    error_log: str,
    job_name: str,
    partition: str,
    # account: str,
    array_dir: Path,
    sbatch_options: str,
    time: str,
    cpus: int,
    memory: str,
    cwd: Path,
    rate_limit: int,
    modules: List[str] = None,
    container_image: str = None,
    container_mounts: str = None,
    dry_run: bool = False
) -> None:
    """
    Builds the submission environment and submits the sbatch command.
    """
    job_count = len(job_scripts)
    logger.debug(f"Preparing to submit array of {job_count} jobs.")
    
    # 1. Format the array string (e.g., "1-10" or "1-10%2" for rate limits)
    rate_limit_str = f"%{rate_limit}" if rate_limit else ""
    job_array_str = f"1-{job_count}{rate_limit_str}"
    
    # 2. Resolve absolute paths for safety
    job_script_path = job_scripts[0].parent.resolve()
    cwd_resolved = cwd.resolve()

    # =========================================================================
    # Slurm submission script. This script uses $SLURM_ARRAY_TASK_ID to 
    # =========================================================================
    master_script_path = array_dir / f"{job_name}_master.sh"
    
    master_script_content = f"""#!/bin/bash
# This is the master entry point for the Swarm job array.
# Slurm will run this script {job_count} times.
# SLURM_ARRAY_TASK_ID will automatically change from 1 to {job_count}.
# Execute the specific job script for this array task:
bash {job_script_path}/job_$SLURM_ARRAY_TASK_ID.sh
"""
    # Save the master script to the disk
    master_script_path.write_text(master_script_content)
    logger.debug(f"Created master submission script at: {master_script_path}")


    # 3. Build the core sbatch command. 
    # Notice we pass the master_script_path at the very end instead of --wrap!
    sbatch_command_parts = [
        "sbatch",
        f"--chdir={cwd_resolved}",
        f"--partition={partition}",
        f"--job-name={job_name}",
        f"--output={output_log}",
        f"--error={error_log}",
        f"--time={time}",
        f"--cpus-per-task={cpus}",
        f"--mem={memory}",
        f"--array={job_array_str}"
    ]

    # 4. Add any custom options the user passed in (e.g., --gres=gpu:1)
    if sbatch_options:
        logger.debug(f"Appending user-provided sbatch_options: {sbatch_options}")
        sbatch_command_parts.extend(sbatch_options.split())

    # =========================================================================
    # CONTAINER SUPPORT (Pyxis / Enroot)
    # =========================================================================
    if container_image:
        logger.debug(f"Adding container image: {container_image}")
        sbatch_command_parts.append(f"--container-image={container_image}")
        
    if container_mounts:
        logger.debug(f"Adding container mounts: {container_mounts}")
        sbatch_command_parts.append(f"--container-mounts={container_mounts}")

    # 5. Append the actual file we want to submit!
    sbatch_command_parts.append(str(master_script_path))

    # 6. Save a text copy of the exact command we are running for the user's records
    sbatch_command_str = " ".join(sbatch_command_parts)
    logger.debug(f"Final constructed sbatch command: {sbatch_command_str}")
    
    sbatch_record_file = array_dir / f"{job_name}_command.txt"
    sbatch_record_file.write_text(sbatch_command_str + "\n")

    # 7. Dry Run Check
    if dry_run:
        logger.info("Dry run flag detected. Skipping subprocess execution.")
        print("\n[DRY RUN] Would submit the following command to Slurm:\n")
        print(sbatch_command_str)
        print(f"\n[DRY RUN] Master script saved to: {master_script_path}")
        return

    # 8. Execution
    try:
        logger.debug("Executing subprocess.run...")
        result = subprocess.run(
            sbatch_command_parts,
            capture_output=True, 
            text=True,           
            check=True           
        )
        logger.info(f"Subprocess succeeded. STDOUT: {result.stdout.strip()}")
        print(f"Success: {result.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess failed! Return code: {e.returncode}")
        logger.error(f"STDERR output: {e.stderr.strip()}")
        raise RuntimeError(f"Slurm submission failed: {e.stderr.strip()}")