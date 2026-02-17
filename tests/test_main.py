import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from swarm.main import app

# Typer provides a fake terminal runner to test CLI commands safely
runner = CliRunner()

@pytest.fixture
def mock_bash_file(tmp_path: Path) -> Path:
    """
    A Pytest fixture that creates a temporary bash file for testing.
    This file is automatically deleted after the tests finish!
    """
    script = tmp_path / "mock_script.sh"
    script.write_text("echo 'Task 1'\necho 'Task 2'\necho 'Task 3'\n")
    return script


# We mock submit_job_array because we already test it in test_slurm.py.
# Here, we only want to test if the CLI correctly passes arguments down.
@patch("swarm.main.submit_job_array")
def test_main_dry_run(mock_submit, mock_bash_file):
    """Test that the CLI correctly parses arguments and runs in dry-run mode."""
    
    result = runner.invoke(app, ["--file", str(mock_bash_file), "--dry-run"])
    
    # Assert the command succeeded
    assert result.exit_code == 0
    assert "Successfully split into 3 array tasks." in result.stdout
    
    # Verify our mock submit function was called
    mock_submit.assert_called_once()
    
    # Verify the dry_run=True flag was passed to the submission layer
    _, kwargs = mock_submit.call_args
    assert kwargs["dry_run"] is True


@patch("swarm.main.submit_job_array")
def test_main_normal_run(mock_submit, mock_bash_file):
    """Test a standard run without the dry-run flag."""
    
    result = runner.invoke(app, ["--file", str(mock_bash_file), "--partition=compute"])
    
    assert result.exit_code == 0
    mock_submit.assert_called_once()
    
    # Verify arguments were parsed correctly
    _, kwargs = mock_submit.call_args
    assert kwargs["partition"] == "compute"
    assert kwargs["dry_run"] is False

@patch("swarm.main.verify_modules") # <--- NEW MOCK
@patch("swarm.main.submit_job_array")
def test_main_with_modules(mock_submit, mock_verify, mock_bash_file): # <--- NEW TEST
    mock_verify.return_value = ["python"]
    
    result = runner.invoke(app, ["--file", str(mock_bash_file), "--modules", "python", "--dry-run"])
    
    assert result.exit_code == 0
    mock_verify.assert_called_once_with("python")

def test_main_missing_file():
    """Test how the CLI handles a user providing a file that doesn't exist."""
    
    result = runner.invoke(app, ["--file", "this_file_is_fake.sh"])
    
    # The exit code should NOT be 0 (0 means success)
    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)
    
