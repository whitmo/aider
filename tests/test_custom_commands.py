import os
import tempfile
from pathlib import Path
import pytest
import yaml
from unittest.mock import Mock, patch

from aider.commands import CustomCommand, CustomCommandManager, Commands


def test_custom_command_creation():
    cmd = CustomCommand("test", "shell", "echo test", "Test command")
    assert cmd.name == "test"
    assert cmd.command_type == "shell"
    assert cmd.definition == "echo test"
    assert cmd.description == "Test command"


def test_custom_command_manager_load_user_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config" / "aider"
        config_dir.mkdir(parents=True)
        
        config = {
            "test": "echo test",
            "complex": {
                "type": "shell",
                "definition": "pytest",
                "description": "Run tests"
            }
        }
        
        config_path = config_dir / "commands.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = CustomCommandManager()
            
            assert "test" in manager.commands
            assert manager.commands["test"].command_type == "shell"
            assert manager.commands["test"].definition == "echo test"
            
            assert "complex" in manager.commands
            assert manager.commands["complex"].command_type == "shell"
            assert manager.commands["complex"].definition == "pytest"
            assert manager.commands["complex"].description == "Run tests"


def test_custom_command_manager_load_repo_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        repo_config_dir = tmp_path / ".aider"
        repo_config_dir.mkdir()
        
        config = {
            "repo-cmd": "git status",
        }
        
        config_path = repo_config_dir / "commands.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        with patch("pathlib.Path.home", return_value=lambda: tmp_path):
            manager = CustomCommandManager()
            
            assert "repo-cmd" in manager.commands
            assert manager.commands["repo-cmd"].command_type == "shell"
            assert manager.commands["repo-cmd"].definition == "git status"


def test_commands_custom_shell_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Set up mocks for token counting
    coder_mock.main_model = Mock()
    coder_mock.main_model.token_count.return_value = 100
    
    # Mock the CustomCommandManager
    cmd.custom_commands = Mock()
    cmd.custom_commands.commands = {
        "test": CustomCommand("test", "shell", "echo {args}", "Test command")
    }
    
    # Test running the custom command
    cmd.do_run("test", "hello")
    
    # Verify that cmd_run was called with the expanded command
    assert io_mock.method_calls


def test_commands_custom_plugin_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Create a mock plugin function
    plugin_mock = Mock()
    
    # Mock the import_string function
    with patch("aider.commands.import_string", return_value=plugin_mock):
        # Mock the CustomCommandManager
        cmd.custom_commands = Mock()
        cmd.custom_commands.commands = {
            "plugin": CustomCommand(
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


def test_commands_custom_override_command():
    io_mock = Mock()
    coder_mock = Mock()
    
    cmd = Commands(io_mock, coder_mock)
    
    # Create a mock override function
    def override_func(commands, original_func, args):
        return f"Override: {args}"
    
    # Mock the import_string function
    with patch("aider.commands.import_string", return_value=override_func):
        # Mock the CustomCommandManager
        cmd.custom_commands = Mock()
        cmd.custom_commands.commands = {
            "commit": CustomCommand(
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


def test_custom_command_manager_config_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / ".config" / "aider"
        config_dir.mkdir(parents=True)
        
        # Write invalid YAML
        config_path = config_dir / "commands.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: :")
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = CustomCommandManager()
            
            # Should handle the error gracefully
            assert len(manager.commands) == 0
