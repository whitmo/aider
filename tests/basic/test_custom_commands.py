import os
import tempfile
from pathlib import Path
import pytest
import yaml
from unittest.mock import Mock, patch

from aider.commands import UserCommand, UserCommandRegistry, Commands


def test_user_command_creation():
    cmd = UserCommand("test", "shell", "echo test", "Test command")
    assert cmd.name == "test"
    assert cmd.command_type == "shell"
    assert cmd.definition == "echo test"
    assert cmd.description == "Test command"


def test_user_command_registry_load_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config" / "aider"
        config_dir.mkdir(parents=True)
        
        config = {
            "commands": {
                "test": "echo test",
                "complex": {
                    "type": "shell",
                    "definition": "pytest",
                    "description": "Run tests"
                }
            }
        }
        
        config_path = config_dir / ".aider.conf.yml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        registry = UserCommandRegistry.from_config([config_path])
            
        assert "test" in registry.commands
        assert registry.commands["test"].command_type == "shell"
        assert registry.commands["test"].definition == "echo test"
        
        assert "complex" in registry.commands
        assert registry.commands["complex"].command_type == "shell"
        assert registry.commands["complex"].definition == "pytest"
        assert registry.commands["complex"].description == "Run tests"


def test_commands_user_shell_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Set up mocks for token counting and other attributes
    coder_mock.main_model = Mock()
    coder_mock.main_model.token_count.return_value = 100
    coder_mock.root = "/"
    coder_mock.cur_messages = []
    
    # Mock the UserCommandRegistry
    cmd.user_commands = Mock()
    cmd.user_commands.commands = {
        "test": UserCommand("test", "shell", "echo {args}", "Test command")
    }
    
    # Test running the user command
    cmd.do_run("test", "hello")
    
    # Verify that cmd_run was called with the expanded command
    assert io_mock.method_calls


def test_commands_user_plugin_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Create a mock plugin function
    plugin_mock = Mock()
    
    # Mock the import_string function
    with patch("aider.commands.import_string", return_value=plugin_mock):
        # Mock the UserCommandRegistry
        cmd.user_commands = Mock()
        cmd.user_commands.commands = {
            "plugin": UserCommand(
                "plugin", 
                "plugin", 
                "my_plugin.func", 
                "Plugin command"
            )
        }
        
        # Test running the plugin command
        cmd.do_run("plugin", "test")
        
        # Verify that the plugin function was called
        plugin_mock.assert_called_once_with(cmd, "test")


def test_commands_user_override_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Create a mock override function
    def override_func(commands, original_func, args):
        return f"Override: {args}"
    
    # Mock the import_string function
    with patch("aider.commands.import_string", return_value=override_func):
        # Mock the UserCommandRegistry
        cmd.user_commands = Mock()
        cmd.user_commands.commands = {
            "commit": UserCommand(
                "commit", 
                "override", 
                "my_plugin.override_commit", 
                "Override commit"
            )
        }
        
        # Test running the override command
        result = cmd.do_run("commit", "test message")
        
        # Verify the result
        assert result == "Override: test message"


def test_user_command_registry_config_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config" / "aider"
        config_dir.mkdir(parents=True)
        
        # Write invalid YAML
        config_path = config_dir / ".aider.conf.yml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: :")
        
        registry = UserCommandRegistry.from_config([config_path])
            
        # Should handle the error gracefully
        assert len(registry.commands) == 0
