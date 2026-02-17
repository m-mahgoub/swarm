import logging
import typer
from pathlib import Path

# Import our core logic modules
from swarm.parser import create_job_scripts
from swarm.slurm import submit_job_array

# Initialize Typer (handles terminal commands and help menus)
app = typer.Typer(help="Swarm: A modern Slurm job array generator.")

def setup_logging(debug_mode: bool):
    """
    Configures the 'Black Box Flight Recorder' (Logging).
    Tracks detailed, technical data behind the scenes safely to a file.
    """
    # 1. ALWAYS save detailed debug logs to a file called swarm.log
    file_handler = logging.FileHandler("swarm.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)

    handlers = [file_handler]

    # 2. If the user passes the --debug flag, ALSO print technical logs to the screen
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter("DEBUG [%(name)s]: %(message)s")
        console_handler.setFormatter(console_format)
        handlers.append(console_handler)

    # 3. Apply these rules to the core Python logging system
    logging.basicConfig(level=logging.DEBUG, handlers=handlers)
    logging.debug("--- Swarm execution started ---")


# @app.callback means this runs immediately when the user types `swarm`
@app.callback(invoke_without_command=True)
def main(
    # MANDATORY OPTION: Only the file is required (...)
    file: str = typer.Option(..., "--file", "-f", help="Input bash file with multiple commands."),
    
    # DIRECTORY CONTROL OPTIONS
    chdir: str = typer.Option(None, "--chdir", "-D", help="Execution directory for the Slurm job. Defaults to the bash file's directory."),
    array_dir: str = typer.Option("sbatch_arrays", "--array_dir", help="Where to save the generated array scripts. Defaults to a folder inside the chdir."),
    
    # OPTIONAL SLURM OPTIONS (With sensible defaults, NO account option)
    partition: str = typer.Option("general-cpu", "--partition", "-p", help="Partition to submit the job."),
    output_log: str = typer.Option("%A_%a.log", "--output_log", "-o", help="Path to the output log file."),
    error_log: str = typer.Option("%A_%a.err", "--error_log", "-e", help="Path to the error log file."),
    time: str = typer.Option("24:00:00", "--time", "-t", help="Wall-clock time for job (e.g., 24:00:00)."),
    cpus: int = typer.Option(4, "--cpus", "-c", help="Number of CPUs per task."),
    memory: str = typer.Option("8G", "--mem", help="Memory requirement (e.g., 8G)."),
    sbatch_options: str = typer.Option("", "--sbatch_options", help="Additional sbatch options (e.g., --gres=gpu:1)."),
    job_name: str = typer.Option("swarm_array", "--job_name", "-J", help="Job name for the job array."),
    rate_limit: int = typer.Option(None, "--rate_limit", help="Job submission rate limit (max simultaneous tasks)."),
    
    # OPTIONAL CONTAINER OPTIONS (Pyxis/Enroot)
    container_image: str = typer.Option(None, "--image", help="Path or URL to the Pyxis/Enroot container image (e.g., ubuntu:latest or /path/to/image.sqsh)."),
    container_mounts: str = typer.Option(None, "--mounts", help="Comma-separated list of container mounts (e.g., /src:/dest,/src2:/dest2)."),
    
    # OPTIONAL DEV FLAGS
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the planned actions without executing them."),
    debug: bool = typer.Option(False, "--debug", help="Enable detailed debug logging to the terminal.")
):
    """
    Parse a bash file and submit it as a Slurm job array.
    """
    # 1. Start the logging system
    setup_logging(debug)
    logger = logging.getLogger(__name__)

    # =========================================================================
    # PATH RESOLUTION LOGIC
    # =========================================================================
    
    # 2a. Resolve the main bash file
    bash_file = Path(file).resolve()
    logger.debug(f"Resolved bash file path: {bash_file}")

    # 2b. Resolve the working directory (chdir)
    if chdir is None:
        # If no chdir provided, default to the directory where the bash file lives
        cwd_path = bash_file.parent
        logger.debug("No --chdir provided. Defaulting to bash file directory.")
    else:
        # Use the user-provided directory and make sure it exists
        cwd_path = Path(chdir).resolve()
        cwd_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"User provided --chdir. Resolved to: {cwd_path}")

    # 2c. Resolve the array_dir relative to the working directory
    # Pathlib magic: If array_dir is absolute (e.g. "/tmp/arrays"), it ignores cwd_path!
    # If array_dir is relative (e.g. "sbatch_arrays"), it combines them safely.
    array_dir_path = (cwd_path / array_dir).resolve()
    array_dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Resolved array scripts directory to: {array_dir_path}")

    # =========================================================================
    # CORE EXECUTION
    # =========================================================================

    # 3. User Interface: Tell the user what we are doing
    typer.secho(f"Processing bash file: {bash_file}", fg=typer.colors.CYAN)
    
    # 4. Parse the file into separate job scripts
    logger.info("Calling parser to create individual job scripts...")
    job_scripts = create_job_scripts(bash_file, array_dir_path)
    
    if not job_scripts:
        logger.error("Parser returned no scripts. Exiting.")
        typer.secho("Error: No valid commands found in the bash file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Successfully split into {len(job_scripts)} array tasks.", fg=typer.colors.GREEN)

    # 5. Submit the array to Slurm
    logger.info("Passing data to Slurm submission module...")
    submit_job_array(
        job_scripts=job_scripts,
        output_log=output_log,
        error_log=error_log,
        job_name=job_name,
        partition=partition,
        # account="",          # Blank since we removed the account requirement
        array_dir=array_dir_path,
        sbatch_options=sbatch_options,
        time=time,
        cpus=cpus,
        memory=memory,
        cwd=cwd_path,        # Pass the calculated working directory
        rate_limit=rate_limit,
        container_image=container_image,
        container_mounts=container_mounts,
        dry_run=dry_run
    )

if __name__ == "__main__":
    app()