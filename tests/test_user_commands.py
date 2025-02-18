import pytest
from pathlib import Path
import tempfile
import yaml

from aider.user_commands import CommandLoader, UserCommand, UserCommandRegistry, CommandLoadError

def test_empty_config():
    """Test that aider starts up without a commands file"""
    loader = CommandLoader([])
    assert loader.load_commands() == {}

def test_missing_config():
    """Test that aider handles missing command files gracefully"""
    loader = CommandLoader(["/nonexistent/path"])
    assert loader.load_commands() == {}

def test_invalid_yaml(caplog):
    """Test handling of invalid YAML files"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        f.write("invalid: yaml: :")
        f.flush()
        loader = CommandLoader([f.name])
        try:
            loader.load_commands_from_file(f.name)
            pytest.fail("Should have raised CommandLoadError")
        except CommandLoadError as e:
            assert "mapping values are not allowed here" in str(e)
            assert "Failed to parse YAML" in str(e)

def test_load_commands_from_file():
    """Test loading commands from a single file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.dump({
            "commands": {
                "test": {
                    "help": "Test command",
                    "definition": "echo test"
                }
            }
        }, f)
        f.flush()
        
        loader = CommandLoader([])
        commands = loader.load_commands_from_file(f.name)
        assert len(commands) == 1
        assert "test" in commands

def test_command_registry_lifecycle():
    """Test the full lifecycle of commands in the registry"""
    registry = UserCommandRegistry()
    
    # Test adding commands
    cmd1 = UserCommand("test1", "shell", "echo test1", "Test command 1")
    cmd2 = UserCommand("test2", "shell", "echo test2", "Test command 2")
    
    registry.add_commands("source1.yaml", {"test1": cmd1})
    registry.add_commands("source2.yaml", {"test2": cmd2})
    
    assert "test1" in registry.commands
    assert "test2" in registry.commands
    assert registry.sources["source1.yaml"] == {"test1"}
    assert registry.sources["source2.yaml"] == {"test2"}
    
    # Test dropping by source
    assert registry.drop_commands("source1.yaml")
    assert "test1" not in registry.commands
    assert "source1.yaml" not in registry.sources
    
    # Test dropping by command name
    assert registry.drop_commands("test2")
    assert "test2" not in registry.commands
    assert not registry.sources
    
    # Test dropping non-existent
    assert not registry.drop_commands("nonexistent")

def test_command_types():
    """Test different command types"""
    loader = CommandLoader([])
    
    # Test shell command
    shell_cmd = loader._create_command("test", "echo test")
    assert shell_cmd.command_type == "shell"
    
    # Test plugin command
    plugin_def = {
        "type": "plugin",
        "definition": "my.plugin.func",
        "help": "Plugin help"
    }
    plugin_cmd = loader._create_command("test", plugin_def)
    assert plugin_cmd.command_type == "plugin"
    
    # Test invalid type
    with pytest.raises(ValueError):
        loader._create_command("test", {"type": "invalid", "definition": "test"})
