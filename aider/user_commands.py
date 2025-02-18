import yaml
from dataclasses import dataclass
from typing import Optional, Dict, Set, Callable
from pathlib import Path
from contextlib import contextmanager
from importlib.metadata import entry_points
import logging

logger = logging.getLogger(__name__)

@contextmanager
def error_handler(io, error_prefix):
    try:
        yield
    except Exception as e:
        io.tool_error(f"{error_prefix}: {e}")


def load_plugin(plugin_spec):
    """Load a plugin from either a dotted path or entry point specification.

    Args:
        plugin_spec (str): Either a dotted path ('package.module.function')
                          or entry point spec ('package#entry_point')

    Returns:
        callable: The loaded plugin function

    Raises:
        ImportError: If the plugin cannot be loaded, with detailed error information
    """
    # Dotted path format: package.module.function
    if not '#' in plugin_spec:
        return import_string(plugin_spec)

    # Entry point format: package#entry_point
    package, entry_point = plugin_spec.split('#', 1)
    group = f'{package}_aider_commands'
    try:
        eps = entry_points(group=group)
        if not eps:
            raise ImportError(f"No entry points found in group {group}")
        if isinstance(eps, dict):  # Handle different entry_points() return types
            if entry_point not in eps:
                raise ImportError(f"Entry point {entry_point} not found in {group}")
            return eps[entry_point].load()

        matching = [ep for ep in eps if ep.name == entry_point]
        if not matching:
            raise ImportError(f"Entry point {entry_point} not found in {group}")
        return matching[0].load()
    except ImportError as e:
        raise e
    except Exception as e:
        raise ImportError(f"Error loading entry point {entry_point} from {group}: {str(e)}")

def import_string(import_name):
    """Import a module path and return the attribute/class designated by the last name."""
    try:
        module_path, class_name = import_name.rsplit('.', 1)
    except ValueError as e:
        raise ImportError(f"{import_name} doesn't look like a module path") from e

    try:
        module = __import__(module_path, None, None, [class_name])
    except ImportError as e:
        raise ImportError(f"Could not import module {module_path}") from e

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Module {module_path} does not define a {class_name} attribute/class") from e

@dataclass
class UserCommand:
    name: str
    command_type: str
    definition: str
    description: Optional[str] = None
    _runner: Optional[Callable] = None

    def __post_init__(self):
        self._dispatch = {
            "shell": self._run_shell,
            "plugin": self._run_plugin,
            "override": self._run_override,
        }
        self._runner = self._dispatch.get(self.command_type)
        if not self._runner:
            raise ValueError(f"Unknown command type: {self.command_type}")

    def __call__(self, commands, args=""):
        return self._runner(commands, args)

    def _run_shell(self, commands, args):
        shell_cmd = self.definition.format(args=args)
        return commands.cmd_run(shell_cmd)

    def _run_plugin(self, commands, args):
        with error_handler(commands.io, f"Error running plugin command {self.name}"):
            plugin_func = load_plugin(self.definition)
            return plugin_func(commands, args)

    def _run_override(self, commands, args):
        with error_handler(commands.io, f"Error running override command {self.name}"):
            override_func = load_plugin(self.definition)
            return override_func(commands, args)

class CommandLoader:
    def __init__(self, config_paths):
        self.config_paths = config_paths

    def load_commands(self) -> dict:
        """Load commands from all config paths."""
        all_commands = {}
        for path in self.config_paths:
            try:
                yaml_content = self._read_yaml(path)
                if not yaml_content:
                    logger.debug(f"No commands found in {path}")
                    continue
                    
                logger.debug(f"Loaded YAML from {path}: {yaml_content}")
                new_commands = self._parse_commands(yaml_content)
                logger.debug(f"Parsed {len(new_commands)} commands from {path}")
                
                # Update all_commands with new commands
                all_commands.update(new_commands)
                logger.debug(f"Command dict now contains: {sorted(all_commands.keys())}")
            except Exception as e:
                logger.error(f"Failed to load commands from {path}: {e}")
                
        logger.debug(f"Final command dict contains {len(all_commands)} commands: {sorted(all_commands.keys())}")
        return all_commands

    def _read_yaml(self, path) -> dict:
        """Read and parse YAML from a file."""
        path = Path(path).expanduser()
        if not path.exists():
            logger.debug(f"File not found: {path}")
            return {}

        try:
            content = path.read_text(encoding='utf-8')
            config = yaml.safe_load(content)
            if config is None:
                logger.debug(f"Empty YAML file: {path}")
                return {}
            logger.debug(f"Loaded YAML from {path}: {config}")
            return config
        except yaml.YAMLError as e:
            logger.warning(f'Failed to parse YAML from {path}: {e}')
            return {}
        except Exception as e:
            logger.warning(f'Error reading file {path}: {e}')
            return {}

    def _parse_commands(self, config: dict) -> dict:
        """Parse commands from YAML config."""
        # Handle both top-level commands and direct command definitions
        user_commands = config.get("commands", config)
        
        if not isinstance(user_commands, dict):
            logger.warning(f"Invalid commands format, expected dict but got: {type(user_commands)}")
            return {}

        commands = {}
        for name, cmd_def in user_commands.items():
            try:
                cmd = self._create_command(name, cmd_def)
                logger.debug(f"Created command {name}: {cmd}")
                commands[name] = cmd
            except (KeyError, ValueError) as e:
                logger.warning(f'Failed to create command {name}: {e}')
                continue

        return commands

    def _create_command(self, name: str, definition) -> UserCommand:
        if isinstance(definition, str):
            return UserCommand(
                name=name,
                command_type="shell",
                definition=definition,
                description=f"Run: {definition}"
            )

        if "definition" not in definition:
            raise KeyError("Command definition must include 'definition' field")

        command_type = definition.get("type", "shell")
        if command_type not in {"shell", "plugin", "override"}:
            raise ValueError(f"Unknown command type: {command_type}")

        help_text = (
            definition.get('help') or
            definition.get('description') or
            f"Run: {definition['definition']}"
        )

        return UserCommand(
            name=name,
            command_type=command_type,
            definition=definition["definition"],
            description=help_text
        )

class UserCommandRegistry:
    def __init__(self, commands=None):
        self.commands = commands or {}
        self.sources: Dict[str, Set[str]] = {}

    @classmethod
    def from_config(cls, config_paths):
        loader = CommandLoader(config_paths)
        registry = cls()
        commands = loader.load_commands()
        if commands:
            registry.add_commands("<config>", commands)
        return registry

    def add_commands(self, path, commands):
        self.sources[path] = set(commands.keys())
        self.commands.update(commands)

    def drop_commands(self, target):
        if target in self.sources:
            for name in self.sources[target]:
                self.commands.pop(name, None)
            del self.sources[target]
            return True
        elif target in self.commands:
            del self.commands[target]
            for src, names in list(self.sources.items()):
                if target in names:
                    names.remove(target)
                    if not names:
                        del self.sources[src]
            return True
        return False

    def list_commands(self, io):
        by_source = {}
        for cmd_name, cmd in self.commands.items():
            source = None
            for src, names in self.sources.items():
                if cmd_name in names:
                    source = src
                    break
            source = source or "<unknown>"
            by_source.setdefault(source, []).append((cmd_name, cmd))

        for source, cmds in sorted(by_source.items()):
            io.tool_output(f"\nCommands from {source}:")
            for name, cmd in sorted(cmds):
                desc = cmd.description or "No description"
                io.tool_output(f"  {name:20} : {desc}")
