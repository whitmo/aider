# User Commands in Aider

Aider provides a command system that can be extended with custom commands. This document covers the core concepts and includes runnable examples.

## Loading Custom Commands

Aider supports three ways to load custom commands:

1. Dotted Path Import:
```yaml
commands:
  hello:
    type: plugin
    definition: mypackage.commands.hello
```

2. Entry Point Import:
```yaml
commands:
  hello:
    type: plugin
    definition: mypackage#hello
```
And in your package's pyproject.toml:
```toml
[project.entry-points."mypackage_aider_commands"]
hello = "mypackage.commands:hello_command"
```

3. Direct YAML File (not implemented yet):
```bash
$ aider --commands /path/to/commands.yaml
```
Or within aider:
```
/cmd add /path/to/commands.yaml
```

## Command Basics

How commands work:

```python
# Create a basic Commands instance for testing
>>> io = InputOutput()
>>> class MockCoder: pass
>>> coder = MockCoder()
>>> cmds = Commands(io, coder)

# Basic command properties
>>> cmd = UserCommand("echo", "shell", "echo {args}")
>>> cmd.name
'echo'
>>> cmd.command_type
'shell'
>>> cmd.definition
'echo {args}'

## Command Types

### Shell Commands

Shell commands execute system commands:

```python
>>> # Simple shell command
>>> date_cmd = UserCommand("date", "shell", "date")
>>> date_cmd.command_type
'shell'

>>> # Shell command with arguments
>>> echo_cmd = UserCommand("echo", "shell", "echo {args}")
>>> echo_cmd.definition
'echo {args}'

### Plugin Commands

Plugin commands add new Python functions:

```python
>>> # Plugin command definition
>>> greet_cmd = UserCommand("greet", "plugin", "mypackage.greetings.say_hello")
>>> greet_cmd.command_type
'plugin'
>>> greet_cmd.definition
'mypackage.greetings.say_hello'

A plugin function should accept these parameters:
- commands: The Commands instance
- args: String of command arguments

Example plugin implementation:
```python
def say_hello(commands, args):
    name = args.strip() or "friend"
    commands.io.tool_output(f"Hello, {name}!")
```

### Override Commands

Override commands modify existing command behavior:

```python
>>> # Override command
>>> add_cmd = UserCommand("add", "override", "mypackage.file_handlers.custom_add")
>>> add_cmd.command_type
'override'

Override functions receive:
- commands: The Commands instance
- original_func: The original command function
- args: Command arguments

Example override:
```python
def custom_add(commands, original_func, args):
    commands.io.tool_output("Pre-processing...")
    result = original_func(args)
    commands.io.tool_output("Post-processing...")
    return result
```

## Command Configuration

Commands can be configured via YAML:

```yaml
commands:
  date:
    type: shell
    definition: "date"
    description: "Show current date/time"

  greet:
    type: plugin
    definition: mypackage.greetings.say_hello
    description: "Greet the user"
```

Loading commands:
```python
>>> from aider.commands import CommandLoader
>>> commands = CommandLoader.load_from(["/path/to/config.yml"])
>>> len(commands) >= 0  # Will vary based on config
True

## Error Handling

Commands handle errors gracefully:

```python
>>> # Invalid command type
>>> cmd = UserCommand("bad", "invalid", "something") # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
ValueError: Unknown command type: invalid
```
