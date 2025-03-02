#!/bin/bash

# Optimized Test Runner for Aider
#
# This script runs tests with optimized sequencing so that slower tests run first
# while faster tests start later. This improves overall test execution time,
# especially when running tests in parallel.
#
# Features:
# - Records test execution times in .test_execution_times.json
# - Sorts tests by execution time (slowest first)
# - Optimizes test ordering for parallel execution
# - Provides statistics about test execution times
#
# Usage:
#   ./run_tests.sh                     # Run all tests with optimized sequencing
#   ./run_tests.sh --auto-parallel     # Run with auto-parallelization
#   ./run_tests.sh -v tests/basic/     # Pass any additional pytest arguments

# Exit on error
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    uv venv .venv
    uv pip install -e ".[dev]" pytest-xdist
fi

# Activate the virtual environment
source .venv/bin/activate

# Run the tests with optimized configuration
echo "Running tests with optimized configuration..."
python -m pytest "$@"

# Display test execution times if available
TIMES_FILE="tests/.test_execution_times.json"
if [ -f "$TIMES_FILE" ]; then
    echo -e "\nTest execution times (sorted by duration):"
    python -c "
import json
import sys
from pathlib import Path

times_file = Path('$TIMES_FILE')
if times_file.exists():
    with open(times_file, 'r') as f:
        times = json.load(f)
    
    # Sort by duration (longest first)
    sorted_times = sorted(times.items(), key=lambda x: x[1], reverse=True)
    
    # Print the top 10 slowest tests
    print('\nTop 10 slowest tests:')
    for i, (test, duration) in enumerate(sorted_times[:10], 1):
        print(f'{i}. {test}: {duration:.2f}s')
    
    # Calculate and print statistics
    if times:
        durations = list(times.values())
        total = sum(durations)
        avg = total / len(durations)
        median = sorted(durations)[len(durations) // 2]
        
        print(f'\nTotal test time: {total:.2f}s')
        print(f'Average test time: {avg:.2f}s')
        print(f'Median test time: {median:.2f}s')
        print(f'Number of tests: {len(times)}')
"
fi

# Deactivate the virtual environment
deactivate

echo -e "\nTests completed."
