from pathlib import Path
from swarm.parser import create_job_scripts

def test_create_job_scripts(tmp_path: Path):
    # tmp_path is a built-in pytest fixture. 
    # It creates a safe temporary folder just for this test!
    
    # 1. Create a fake input bash file
    mock_bash = tmp_path / "test_input.sh"
    mock_bash.write_text("""
# This is a comment
ls -l

# Next command is multiline
echo 'hello' \\
  'world'
""")

    # 2. Create the output directory
    array_dir = tmp_path / "arrays"
    array_dir.mkdir()

    # 3. Run our function
    job_scripts = create_job_scripts(mock_bash, array_dir)

    # 4. Assertions to prove it worked
    assert len(job_scripts) == 2
    
    # Check the first job
    assert job_scripts[0].name == "job_1.sh"
    assert job_scripts[0].read_text().strip() == "ls -l"
    
    # Check the second job (multiline string joined properly)
    assert job_scripts[1].name == "job_2.sh"
    assert "echo 'hello' 'world'" in job_scripts[1].read_text()
    
def test_create_job_scripts_with_modules(tmp_path: Path): # <--- NEW
    mock_bash = tmp_path / "test_input.sh"
    mock_bash.write_text("ls -l")
    array_dir = tmp_path / "arrays"
    array_dir.mkdir()

    # Pass a list of modules
    job_scripts = create_job_scripts(mock_bash, array_dir, modules=["python/3.9", "gcc"])

    assert len(job_scripts) == 1
    content = job_scripts[0].read_text()
    
    # Verify module load is prepended correctly
    assert "module load python/3.9 gcc && ls -l" in content