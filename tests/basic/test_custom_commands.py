import os
import tempfile
import codecs

import textwrap
from pathlib import Path
import pytest
import yaml
from unittest.mock import Mock, patch
from typing import Dict, Any

import git
import pyperclip
from io import StringIO


from aider.commands import UserCommand, UserCommandRegistry, Commands, SwitchCoder
from aider.user_commands import CommandLoader, CommandLoadError
from aider.io import InputOutput
from aider.models import Model
from aider.utils import ChdirTemporaryDirectory, GitTemporaryDirectory, make_repo


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
def test_command_loading(temp_yaml_file, command_loader, yaml_content: str, expected: Dict[str, Any], caplog):
    """Test command loading with various YAML formats."""
    caplog.set_level("DEBUG")

    yaml_file = temp_yaml_file(yaml_content)
    loader = CommandLoader([str(yaml_file)])

    # First check the YAML parsing
    yaml_data = loader._read_yaml(str(yaml_file))
    assert yaml_data, f"Failed to parse YAML content:\n{yaml_content}"

    # Then check command parsing
    parsed_commands = loader._parse_commands(yaml_data)
    assert parsed_commands, f"Failed to parse commands from YAML:\n{yaml_data}"

    # Finally check the full loading
    commands = loader.load_commands()

    name = expected["name"]
    assert name in commands, f"Command {name} not found in loaded commands. Debug logs:\n{caplog.text}"
    cmd = commands[name]

    assert cmd.name == name
    assert cmd.definition == expected["definition"]
    assert cmd.description == expected["help_text"]
    assert cmd.command_type == expected["type"]

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
def test_command_loading(temp_yaml_file, command_loader, yaml_content: str, expected: Dict[str, Any], caplog):
    """Test command loading with various YAML formats."""
    caplog.set_level("DEBUG")

    yaml_file = temp_yaml_file(yaml_content)
    loader = CommandLoader([str(yaml_file)])

    # First check the YAML parsing
    yaml_data = loader._read_yaml(str(yaml_file))
    assert yaml_data, f"Failed to parse YAML content:\n{yaml_content}"

    # Then check command parsing
    parsed_commands = loader._parse_commands(yaml_data)
    assert parsed_commands, f"Failed to parse commands from YAML:\n{yaml_data}"

    # Finally check the full loading
    commands = loader.load_commands()

    name = expected["name"]
    assert name in commands, f"Command {name} not found in loaded commands. Debug logs:\n{caplog.text}"
    cmd = commands[name]

    assert cmd.name == name
    assert cmd.definition == expected["definition"]
    assert cmd.description == expected["help_text"]
    assert cmd.command_type == expected["type"]

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

        commands = CommandLoader.load_from([config_path])
        registry = UserCommandRegistry()
        registry.add_commands(str(config_path), commands)

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

    # Create a real UserCommandRegistry with a test command
    cmd.user_commands = UserCommandRegistry(parent=cmd)
    cmd.user_commands.add_commands(
        "test.yaml",
        {"test": UserCommand("test", "shell", "echo {args}", "Test command")}
    )

    # Test running the user command
    cmd.do_run("test", "hello")

    # Verify that tool_output was called
    io_mock.tool_output.assert_called()


def test_commands_user_plugin_command():
    io_mock = Mock()
    coder_mock = Mock()

    cmd = Commands(io_mock, coder_mock)

    # Create a mock plugin function
    plugin_mock = Mock()

    # Mock the import_string function
    with patch("aider.user_commands.import_string", return_value=plugin_mock):
        # Create a real UserCommandRegistry with a plugin command
        cmd.user_commands = UserCommandRegistry(parent=cmd)
        cmd.user_commands.add_commands(
            "test.yaml",
            {"plugin": UserCommand(
                "plugin",
                "plugin",
                "my_plugin.func",
                "Plugin command"
            )}
        )

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
    with patch("aider.user_commands.import_string", return_value=override_func):
        # Create a real UserCommandRegistry with an override command
        cmd.user_commands = UserCommandRegistry(parent=cmd)
        cmd.user_commands.add_commands(
            "test.yaml",
            {"commit": UserCommand(
                "commit",
                "override",
                "my_plugin.override_commit",
                "Override commit"
            )}
        )

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

        registry = UserCommandRegistry()
        try:
            commands = CommandLoader.load_from([config_path])
            registry.add_commands(str(config_path), commands)
        except CommandLoadError:
            pass

        # Should handle the error gracefully
        assert len(registry.commands) == 0

# Command loader tests
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

@pytest.fixture
def temp_yaml_file(tmp_path):
    """Fixture to create and cleanup temporary YAML files."""
    def _create_yaml(content: str, filename: str = "commands.yaml") -> Path:
        yaml_file = tmp_path / filename
        yaml_file.write_text(content.strip())
        return yaml_file
    return _create_yaml

@pytest.fixture
def command_loader():
    return CommandLoader([])

@pytest.fixture
def gpt35():
    return Model("gpt-3.5-turbo")

@pytest.fixture
def io():
    return InputOutput(pretty=False, fancy_input=False, yes=True)

@pytest.fixture
def commands(io, gpt35):
    from aider.coders import Coder
    coder = Coder.create(gpt35, None, io)
    return Commands(io, coder)

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
