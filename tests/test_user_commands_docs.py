import doctest
import os
from pathlib import Path

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
