# Custom Commands

Aider supports extending its functionality through custom commands defined in YAML configuration files. You can add shell commands, plugins, or override existing commands to customize your workflow.

## Quick Start

1. Create a YAML file (e.g., `commands.yaml`) with your custom commands:

```yaml
commands:
  test:
    help: "Run the test suite"
    definition: "pytest"
  
  lint:
    help: "Run the linter"
    definition: "flake8"
```

2. Add the commands to aider:

```
/cmd add commands.yaml
```

3. List available commands:

```
/cmd list
```

4. Use your commands:

```
/test
/lint
```

## Command Types

### Shell Commands

The simplest type of command executes shell commands:

```yaml
commands:
  build:
    help: "Build the project"
    definition: "make build"
  
  deploy:
    help: "Deploy to staging"
    definition: "kubectl apply -f k8s/"
```

Shell commands can use `{args}` to include arguments passed to the command:

```yaml
commands:
  branch:
    help: "Create and checkout a new git branch"
    definition: "git checkout -b {args}"
```

Usage: `/branch feature/new-stuff`

### Plugin Commands

For more complex functionality, you can create Python plugin commands:

```yaml
commands:
  analyze:
    type: plugin
    help: "Analyze code complexity"
    definition: "mypackage.complexity.analyze_code"
```

The plugin function should accept two parameters:
- `commands`: The Commands instance
- `args`: String arguments passed to the command

Example plugin implementation:

```python
def analyze_code(commands, args):
    # Access the coder, io, and other aider components
    coder = commands.coder
    io = commands.io
    
    # Your custom logic here
    io.tool_output("Analyzing code...")
```

### Override Commands

You can override built-in commands to customize their behavior:

```yaml
commands:
  commit:
    type: override
    help: "Custom commit behavior"
    definition: "mypackage.git.custom_commit"
```

Override functions receive three parameters:
- `commands`: The Commands instance
- `original_func`: The original command function
- `args`: String arguments passed to the command

Example override:

```python
def custom_commit(commands, original_func, args):
    # Pre-commit hooks
    commands.io.tool_output("Running pre-commit checks...")
    
    # Call original commit function
    result = original_func(args)
    
    # Post-commit actions
    commands.io.tool_output("Notifying CI system...")
    return result
```

## Command Management

Aider provides several commands to manage your custom commands:

- `/cmd add <file.yaml>`: Add commands from a YAML file
- `/cmd drop <name>`: Remove a specific command
- `/cmd drop <file.yaml>`: Remove all commands from a file
- `/cmd list`: List all available commands and their sources

## Configuration Location

Aider looks for command configurations in:

1. The current directory: `.aider.conf.yml`
2. User config directory: `~/.config/aider/.aider.conf.yml`
3. Additional files specified with `/cmd add`

## Best Practices

1. Group related commands in separate YAML files
2. Provide clear help text for each command
3. Use meaningful command names
4. Consider using plugins for complex operations
5. Test commands thoroughly before sharing

## Examples

### Git Workflow Commands

```yaml
commands:
  pr:
    help: "Create a pull request"
    definition: "gh pr create --fill"
  
  sync:
    help: "Sync with upstream"
    definition: |
      git fetch upstream
      git rebase upstream/main
```

### Development Tools

```yaml
commands:
  format:
    help: "Format code"
    definition: |
      black .
      isort .
  
  check:
    help: "Run all checks"
    definition: |
      pytest
      flake8
      mypy .
```

### Project-Specific Commands

```yaml
commands:
  serve:
    help: "Start development server"
    definition: "python manage.py runserver"
  
  migrate:
    help: "Run database migrations"
    definition: "python manage.py migrate"
```
