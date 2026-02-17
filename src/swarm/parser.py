import logging
from pathlib import Path
from typing import List

# Best Practice: Name the logger after the current module (swarm.parser)
logger = logging.getLogger(__name__)

def create_job_scripts(bash_file: Path, array_dir: Path) -> List[Path]:
    logger.debug(f"Starting parsing for file: {bash_file.resolve()}")
    
    job_scripts: List[Path] = []
    current_command: List[str] = []
    inside_command = False

    lines = bash_file.read_text().splitlines()
    logger.debug(f"Read {len(lines)} lines from bash file.")

    for line_num, line in enumerate(lines, start=1):
        stripped_line = line.strip()

        if not stripped_line or stripped_line.startswith('#'):
            continue

        if stripped_line.endswith('\\'):
            current_command.append(stripped_line[:-1].strip())
            inside_command = True
        else:
            current_command.append(stripped_line)
            inside_command = False
            
            full_command = ' '.join(current_command).strip()
            current_command = []

            if full_command:
                job_script = array_dir / f"job_{len(job_scripts) + 1}.sh"
                job_script.write_text(full_command + "\n")
                job_scripts.append(job_script)
                # Log the exact command being written
                logger.debug(f"Created {job_script.name} with command: {full_command}")

    logger.info(f"Successfully generated {len(job_scripts)} job scripts in {array_dir}")
    return job_scripts