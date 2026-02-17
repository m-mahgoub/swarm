import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from swarm.slurm import submit_job_array

def test_submit_job_array_dry_run(tmp_path: Path, capsys):
    """
    Tests that the Slurm submission command is formatted correctly,
    the master script is generated, and --dry-run prevents execution.
    """
    # 1. Setup fake directories and files
    array_dir = tmp_path / "arrays"
    array_dir.mkdir()
    
    job_script = array_dir / "job_1.sh"
    job_script.write_text("echo test")
    
    cwd_path = tmp_path / "work"
    cwd_path.mkdir()

    # 2. Call the function in DRY RUN mode
    submit_job_array(
        job_scripts=[job_script],
        output_log="out.log",
        error_log="err.log",
        job_name="my_test_job",
        partition="general-cpu",
        # account="",
        array_dir=array_dir,
        sbatch_options="--gres=gpu:1 --mail-type=ALL", # Testing option splitting
        time="12:00:00",
        cpus=2,
        memory="16G",
        cwd=cwd_path,
        rate_limit=5,
        container_image="ubuntu:latest",
        container_mounts="/src:/dest",  
        dry_run=True  # Safety first!
    )

    # 3. Verify the Master Script was created correctly
    master_script = array_dir / "my_test_job_master.sh"
    assert master_script.exists()
    master_content = master_script.read_text()
    assert "bash" in master_content
    assert "job_$SLURM_ARRAY_TASK_ID.sh" in master_content
    
    # 4. Verify the Command Record file was created correctly
    command_file = array_dir / "my_test_job_command.txt"
    assert command_file.exists()
    command_content = command_file.read_text()
    
    # 5. Check the sbatch arguments inside the saved file
    assert "sbatch" in command_content
    assert f"--chdir={cwd_path.resolve()}" in command_content
    assert "--partition=general-cpu" in command_content
    assert "--array=1-1%5" in command_content  # 1 job, max 5 at a time
    assert "--gres=gpu:1" in command_content
    assert "--mail-type=ALL" in command_content
    assert "--container-image=ubuntu:latest" in command_content  # <-- NEW
    assert "--container-mounts=/src:/dest" in command_content    # <-- NEW
    assert str(master_script) in command_content  # Master script is at the end

    # 6. Verify stdout says DRY RUN
    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out


# @patch acts as a "stunt double". Whenever our code tries to call 
# subprocess.run inside swarm.slurm, it calls our fake `mock_run` instead!
@patch("swarm.slurm.subprocess.run")
def test_submit_job_array_live_run(mock_run, tmp_path: Path):
    """
    Tests the actual execution path by 'mocking' (faking) the Slurm cluster.
    """
    # 1. Setup our fake Slurm terminal output
    mock_result = MagicMock()
    mock_result.stdout = "Submitted batch job 999999\n"
    mock_run.return_value = mock_result

    # 2. Setup fake file
    array_dir = tmp_path / "arrays"
    array_dir.mkdir()
    job_script = array_dir / "job_1.sh"
    job_script.write_text("echo test")

    # 3. Call the function in LIVE mode
    submit_job_array(
        job_scripts=[job_script],
        output_log="out.log",
        error_log="err.log",
        job_name="live_test",
        partition="general-cpu",
        # account="",
        array_dir=array_dir,
        sbatch_options="",
        time="01:00:00",
        cpus=1,
        memory="4G",
        cwd=tmp_path,
        rate_limit=None,
        container_image=None,
        container_mounts=None,
        dry_run=False  # LIVE RUN!
    )

    # 4. Verify our stunt double was called exactly once
    mock_run.assert_called_once()
    
    # 5. Inspect WHAT arguments our code tried to pass to the stunt double
    args, kwargs = mock_run.call_args
    command_list = args[0]
    
    # Verify the core list structure is intact
    assert command_list[0] == "sbatch"
    assert "--job-name=live_test" in command_list
    assert kwargs["capture_output"] is True