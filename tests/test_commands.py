import pytest
from pathlib import Path
import tempfile
import yaml
from typing import Dict, Any

from aider.commands import CommandLoader, UserCommand, UserCommandRegistry

@pytest.fixture
def temp_yaml_file():
    """Fixture to create and cleanup temporary YAML files."""
    def _create_yaml(content: str) -> Path:
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "commands.yaml"
            yaml_file.write_text(content)
            return yaml_file
    return _create_yaml

@pytest.fixture
def command_loader():
    """Fixture for a clean CommandLoader instance."""
    return CommandLoader([])

@pytest.mark.parametrize("yaml_content,expected", [
    # Test basic command with help
    ("""
    commands:
      test1:
        help: "Test command 1"
        definition: echo test1
    """, {
        "name": "test1",
        "help_text": "Test command 1",
        "definition": "echo test1",
        "type": "shell"
    }),
    
    # Test command without top-level commands key
    ("""
    test2:
      help: "Test command 2"
      definition: echo test2
    """, {
        "name": "test2",
        "help_text": "Test command 2",
        "definition": "echo test2",
        "type": "shell"
    }),
    
    # Test using description instead of help
    ("""
    commands:
      test3:
        description: "Test command 3"
        definition: echo test3
    """, {
        "name": "test3",
        "help_text": "Test command 3",
        "definition": "echo test3",
        "type": "shell"
    }),
    
    # Test with both help and description (help should win)
    ("""
    commands:
      test4:
        help: "Help text"
        description: "Description text"
        definition: echo test4
    """, {
        "name": "test4",
        "help_text": "Help text",
        "definition": "echo test4",
        "type": "shell"
    }),
    
    # Test with neither help nor description
    ("""
    commands:
      test5:
        definition: echo test5
    """, {
        "name": "test5",
        "help_text": "Run: echo test5",
        "definition": "echo test5",
        "type": "shell"
    }),
    
    # Test custom command type
    ("""
    commands:
      test6:
        type: plugin
        help: "Plugin command"
        definition: my.plugin.func
    """, {
        "name": "test6",
        "help_text": "Plugin command",
        "definition": "my.plugin.func",
        "type": "plugin"
    }),
])
def test_command_loading(temp_yaml_file, command_loader, yaml_content: str, expected: Dict[str, Any]):
    """Test command loading with various YAML formats."""
    yaml_file = temp_yaml_file(yaml_content)
    loader = CommandLoader([str(yaml_file)])
    commands = loader.load_commands()
    
    name = expected["name"]
    assert name in commands, f"Command {name} not found in loaded commands"
    cmd = commands[name]
    
    assert cmd.name == name
    assert cmd.definition == expected["definition"]
    assert cmd.description == expected["help_text"]
    assert cmd.command_type == expected["type"]

def test_command_loading_errors(command_loader):
    """Test error cases in command loading."""
    with pytest.raises(KeyError, match="definition"):
        command_loader._create_command("bad", {"help": "Missing definition"})
    
    with pytest.raises(ValueError, match="Unknown command type"):
        command_loader._create_command("bad", {
            "type": "invalid",
            "definition": "echo bad"
        })

def test_multiple_command_files(temp_yaml_file):
    """Test loading commands from multiple files."""
    file1 = temp_yaml_file("""
    commands:
      cmd1:
        help: "Command 1"
        definition: echo cmd1
    """)
    
    file2 = temp_yaml_file("""
    cmd2:
      help: "Command 2"
      definition: echo cmd2
    """)
    
    loader = CommandLoader([str(file1), str(file2)])
    commands = loader.load_commands()
    
    assert len(commands) == 2
    assert "cmd1" in commands
    assert "cmd2" in commands

def test_command_registry():
    """Test the UserCommandRegistry functionality."""
    registry = UserCommandRegistry()
    
    # Test adding commands
    commands = {
        "test": UserCommand(
            name="test",
            command_type="shell",
            definition="echo test",
            description="Test command"
        )
    }
    registry.add_commands("test.yaml", commands)
    assert "test" in registry.commands
    
    # Test dropping commands
    assert registry.drop_commands("test.yaml")
    assert "test" not in registry.commands
    
    # Test dropping non-existent commands
    assert not registry.drop_commands("nonexistent.yaml")
