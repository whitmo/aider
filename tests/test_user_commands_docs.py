import doctest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
import pytest

from aider.commands import UserCommand, UserCommandRegistry, load_plugin, Commands

def test_user_commands_docs():
    # Get the path to the docs directory relative to this test file
    test_dir = Path(__file__).parent
    docs_file = test_dir.parent / "aider" / "website" / "docs" / "user_commands.md"
    
    # Run doctests on the markdown file
    results = doctest.testfile(
        str(docs_file),
        module_relative=False,
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
    )
    
    # Check if any tests failed
    assert results.failed == 0, f"{results.failed} doctest(s) failed in user_commands.md"

def test_command_loading_methods():
    """Test all three ways of loading commands"""
    io_mock = Mock()
    cmds = Commands(io_mock, None)
    cmds.user_commands = UserCommandRegistry()

    # 1. Dotted path import
    cmd_def = {
        "type": "plugin",
        "definition": "mypackage.commands.hello"
    }
    cmd = UserCommand("hello", cmd_def["type"], cmd_def["definition"])
    
    # 2. Entry point import 
    cmd_def = {
        "type": "plugin", 
        "definition": "mypackage#hello"
    }
    cmd = UserCommand("hello", cmd_def["type"], cmd_def["definition"])

    # 3. Direct import from YAML file
    yaml_content = """
    commands:
      hello:
        type: plugin
        definition: mypackage.commands.hello
    """
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(yaml_content)
        f.flush()
        cmds.cmd_cmd(f"add {f.name}")

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
