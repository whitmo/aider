# User-Defined Commands in Aider

You can extend aider with custom commands using YAML configuration. There are three types of commands:

## Shell Commands

The simplest type - runs a shell command and optionally captures output:

```yaml
commands:
  date:                     # simplest form - just the shell command
    type: shell
    definition: "date"
    description: "Show current date and time"
  
  echo:                     # uses {args} placeholder
    type: shell 
    definition: "echo {args}"
    description: "Echo arguments back"
```

```python
>>> from aider.commands import UserCommand, Commands
>>> cmd = UserCommand("echo", "shell", "echo {args}")
>>> cmd.definition
'echo {args}'
>>> cmd.name
'echo'
```

## Plugin Commands

## Plugin Commands

Plugin commands let you add new Python functions:

```yaml
commands:
  greet:
    type: plugin
    definition: mypackage.greetings.say_hello
    description: "Greet the user"
```

```python
>>> cmd = UserCommand("greet", "plugin", "mypackage.greetings.say_hello") 
>>> cmd.command_type
'plugin'
```

The plugin function should accept two parameters:
- commands: The Commands instance
- args: String of command arguments

Example plugin implementation:
```python
def say_hello(commands, args):
    name = args.strip() or "friend"
    commands.io.tool_output(f"Hello, {name}!")
```

## Override Commands

Override commands can modify existing command behavior:

```yaml
commands:
  add:
    type: override
    definition: mypackage.file_handlers.custom_add
    description: "Custom file add behavior"
```

```python
>>> cmd = UserCommand("add", "override", "mypackage.file_handlers.custom_add")
>>> cmd.command_type
'override'
```

Override functions receive three parameters:
- commands: The Commands instance  
- original_func: The original command function
- args: String of command arguments

Example override implementation:
```python
def custom_add(commands, original_func, args):
    # Do something before
    commands.io.tool_output("Pre-processing files...")
    
    # Call original implementation
    result = original_func(args)
    
    # Do something after
    commands.io.tool_output("Post-processing files...")
    return result
```

## Loading Commands

Commands are loaded from your aider config file:

```python
>>> from aider.commands import CommandLoader
>>> loader = CommandLoader(["/path/to/config.yml"])
>>> registry = loader.load_commands()
>>> len(registry) >= 0  # Will vary based on config
True
```

## Error Handling

Commands handle errors gracefully:

```python
>>> cmd = UserCommand("bad", "invalid", "something")  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
ValueError: Unknown command type: invalid
```
