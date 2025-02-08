import pytest
from pathlib import Path
import tempfile
import yaml

from aider.commands import CommandLoader, UserCommand, UserCommandRegistry

def test_command_loading_formats():
    # Create temp files with different YAML formats
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test file with top-level commands key
        with_commands = Path(tmpdir) / "with_commands.yaml"
        with_commands.write_text("""
# no step on snek

commands:
  test1:
    help: "Test command 1"
    definition: echo test1
""")

        # Test file without top-level commands key
        without_commands = Path(tmpdir) / "without_commands.yaml"
        without_commands.write_text("""
# no step on snek

test2:
  help: "Test command 2"
  definition: echo test2
""")

        # Test loading both formats
        loader = CommandLoader([str(with_commands), str(without_commands)])
        commands = loader.load_commands()
        
        # Verify both commands were loaded
        assert "test1" in commands
        assert "test2" in commands
        
        # Verify command properties
        assert commands["test1"].name == "test1"
        assert "Test command 1" in commands["test1"].description
        assert commands["test1"].definition == "echo test1"
        assert commands["test2"].name == "test2"
        assert "Test command 2" in commands["test2"].description
        assert commands["test2"].definition == "echo test2"
