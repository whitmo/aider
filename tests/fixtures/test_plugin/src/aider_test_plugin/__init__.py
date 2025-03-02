def test_command(commands, args):
    """Test command implementation"""
    commands.io.tool_output(f"Test command called with args: {args}")
    return True

def test_override(commands, original_func, args):
    """Test override implementation"""
    commands.io.tool_output("Pre-processing...")
    result = original_func(args) 
    commands.io.tool_output("Post-processing...")
    return result
