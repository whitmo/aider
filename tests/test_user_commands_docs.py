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

def test_command_loading_methods(tmp_path):
    """Test all three ways of loading commands with real test plugin"""
    # Setup test plugin package
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    
    # Copy test plugin files from fixtures
    import shutil
    fixtures_dir = Path(__file__).parent / "fixtures" / "test_plugin"
    shutil.copytree(fixtures_dir, plugin_dir, dirs_exist_ok=True)
    
    # Install test plugin package
    import subprocess
    subprocess.check_call(["pip", "install", "-e", str(plugin_dir)])

    io_mock = Mock()
    cmds = Commands(io_mock, None)
    cmds.user_commands = UserCommandRegistry()

    # 1. Test entry point loading
    cmd_def = {
        "type": "plugin",
        "definition": "aider_test_plugin#test"
    }
    cmd = UserCommand("test", cmd_def["type"], cmd_def["definition"])
    assert cmd.command_type == "plugin"
    
    # Execute command
    cmd(cmds, "test args")
    io_mock.tool_output.assert_called_with("Test command called with args: test args")

    # Reset mock between tests
    io_mock.reset_mock()

    # 2. Test override command
    cmd_def = {
        "type": "override",
        "definition": "aider_test_plugin#override"
    }
    cmd = UserCommand("test", cmd_def["type"], cmd_def["definition"])
    assert cmd.command_type == "override"

    # Execute override
    def original_func(args):
        return "original result"
    
    cmd(cmds, original_func, "test args")
    assert io_mock.tool_output.call_args_list == [
        Mock(args=("Pre-processing...",)),
        Mock(args=("Post-processing...",))
    ]

    # 3. Test loading via YAML
    yaml_content = """
    commands:
      test:
        type: plugin
        definition: aider_test_plugin#test
    """
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(yaml_content)
        f.flush()
        cmds.cmd_cmd(f"add {f.name}")
        
    # Verify command was loaded
    assert "test" in cmds.user_commands.commands

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
