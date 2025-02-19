from aider.commands import UserCommand, UserCommandRegistry, load_plugin, Commands

import doctest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

import textwrap



@pytest.fixture
def io_mock():
    return Mock()


@pytest.fixture
def commands(io_mock):
    cmds = Commands(io_mock, None)
    cmds.user_commands = UserCommandRegistry()
    return cmds


@pytest.fixture
def plugin_dir(tmp_path):
    """Set up test plugin directory"""
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()

    # Copy test plugin files from fixtures
    fixtures_dir = Path(__file__).parent / "fixtures" / "test_plugin"
    import shutil

    shutil.copytree(fixtures_dir, plugin_dir, dirs_exist_ok=True)

    # Install test plugin package
    import subprocess

    subprocess.check_call(["pip", "install", "-e", str(plugin_dir)])

    return plugin_dir


def test_user_commands_docs():
    """Test user commands documentation"""
    test_dir = Path(__file__).parent
    docs_file = (
        test_dir.parent.parent / "aider" / "website" / "docs" / "user_commands.md"
    )

    # Add setup code that will be prepended to the markdown content
    setup = textwrap.dedent(
        """
        >>> import os
        >>> import tempfile
        >>> from pathlib import Path
        >>> from unittest.mock import Mock, patch
        >>> from aider.io import InputOutput
        >>> from aider.commands import UserCommand, UserCommandRegistry, load_plugin, Commands
        """
    )

    results = doctest.testfile(
        str(docs_file),
        module_relative=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
        setUp=lambda: None,  # Can add setup if needed
        globs={"__file__": str(docs_file)},  # Add any needed globals
    )

    assert results.failed == 0, (
        f"{results.failed} doctest(s) failed in user_commands.md"
    )


def test_entry_point_loading(commands, plugin_dir):
    """Test loading commands via entry points"""
    cmd_def = {"type": "plugin", "definition": "aider_test_plugin#test"}
    cmd = UserCommand("test", cmd_def["type"], cmd_def["definition"])
    assert cmd.command_type == "plugin"

    cmd(commands, "test args")
    commands.io.tool_output.assert_called_with(
        "Test command called with args: test args"
    )


def test_override_command(commands, plugin_dir):
    """Test override command functionality"""
    cmd_def = {"type": "override", "definition": "aider_test_plugin#override"}
    cmd = UserCommand("test", cmd_def["type"], cmd_def["definition"])
    assert cmd.command_type == "override"

    def original_func(args):
        commands.io.tool_output("Original function called")
        return "original result"

    cmd(commands, original_func, "test args")
    assert commands.io.tool_output.call_args_list == [
        Mock(args=("Pre-processing...",)),
        Mock(args=("Original function called",)),
        Mock(args=("Post-processing...",)),
    ]


def test_yaml_loading(commands, plugin_dir):
    """Test loading commands from YAML"""
    yaml_content = """
    commands:
      test:
        type: plugin
        definition: aider_test_plugin#test
    """
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(yaml_content)
        f.flush()
        commands.cmd_cmd(f"add {f.name}")

    assert "test" in commands.user_commands.commands


def test_plugin_loading_errors():
    """Test error handling for plugin loading"""
    with pytest.raises(ImportError):
        load_plugin("nonexistent#command")

    with pytest.raises(ImportError):
        load_plugin("nonexistent.module.function")


def test_command_registry_operations():
    """Test UserCommandRegistry add/drop operations"""
    registry = UserCommandRegistry()

    # Test adding commands
    cmds = {"test": UserCommand("test", "shell", "echo test")}
    registry.add_commands("test.yaml", cmds)
    assert "test" in registry.commands

    # Test dropping by name
    registry.drop_commands("test")
    assert "test" not in registry.commands

    # Test dropping by source
    registry.add_commands("test.yaml", cmds)
    registry.drop_commands("test.yaml")
    assert "test" not in registry.commands
