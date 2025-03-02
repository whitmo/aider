
"""
Pytest plugin for optimized test sequencing.

This plugin records test execution times and uses them to sequence tests so that
slower tests run first while faster tests start later. This improves overall test
execution time, especially when running tests in parallel.

Features:
- Records test execution times in .test_execution_times.json
- Sorts tests by execution time (slowest first)
- Categorizes tests as "slow" or "fast" based on median execution time
- Optimizes test ordering for parallel execution
- Adds a --auto-parallel option to automatically determine optimal parallelization

Usage:
- First run: Tests execute in default order, execution times are recorded
- Subsequent runs: Tests are ordered based on execution times (slowest first)
"""

import json
import os
import time
from pathlib import Path

import pytest

# File to store test execution times
EXECUTION_TIMES_FILE = Path(__file__).parent / ".test_execution_times.json"


def load_execution_times():
    """Load test execution times from file."""
    if not EXECUTION_TIMES_FILE.exists():
        return {}
    
    try:
        with open(EXECUTION_TIMES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If file is corrupted or can't be read, start fresh
        return {}


def save_execution_times(execution_times):
    """Save test execution times to file."""
    try:
        with open(EXECUTION_TIMES_FILE, "w") as f:
            json.dump(execution_times, f, indent=2)
    except IOError:
        # If we can't write to the file, just continue
        pass


class TimedTestRunner:
    """Custom test runner that times test execution."""
    
    def __init__(self, config):
        self.config = config
        self.execution_times = load_execution_times()
        
    def pytest_runtest_protocol(self, item, nextitem):
        """Time the execution of each test."""
        nodeid = item.nodeid
        start_time = time.time()
        
        # Let pytest handle the test execution
        result = None
        
        def fin():
            nonlocal result
            end_time = time.time()
            duration = end_time - start_time
            self.execution_times[nodeid] = duration
            return result
            
        # Use the pytest hook system to run the test
        result = item.ihook.pytest_runtest_protocol(item=item, nextitem=nextitem)
        return fin()
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Save execution times at the end of the test session."""
        save_execution_times(self.execution_times)


class OptimizedTestSorter:
    """Sort test items by execution time (slowest first) and optimize for parallel execution."""
    
    def __init__(self, config):
        self.config = config
        self.execution_times = load_execution_times()
        
    def pytest_collection_modifyitems(self, items, config):
        """Reorder test items based on execution time and optimize for parallel execution."""
        # Skip if no execution times are available
        if not self.execution_times:
            return
        
        # First, categorize tests as slow or fast based on execution time
        slow_tests = []
        fast_tests = []
        
        # Use median time as threshold if we have enough data
        if len(self.execution_times) > 5:
            times = list(self.execution_times.values())
            threshold = sorted(times)[len(times) // 2]  # median
        else:
            # Default threshold of 1 second if not enough data
            threshold = 1.0
        
        for item in items:
            time = self.execution_times.get(item.nodeid, 0)
            if time > threshold:
                slow_tests.append(item)
            else:
                fast_tests.append(item)
        
        # Sort slow tests by execution time (slowest first)
        slow_tests.sort(
            key=lambda item: self.execution_times.get(item.nodeid, 0),
            reverse=True
        )
        
        # Sort fast tests by execution time (fastest first)
        # This helps with load balancing in parallel execution
        fast_tests.sort(
            key=lambda item: self.execution_times.get(item.nodeid, 0)
        )
        
        # Replace items with our optimized order: slow tests first, then fast tests
        items[:] = slow_tests + fast_tests


def pytest_configure(config):
    """Register the plugin with pytest."""
    # Register the test runner
    config.pluginmanager.register(TimedTestRunner(config), "timed_test_runner")
    
    # Register the optimized test sorter
    config.pluginmanager.register(OptimizedTestSorter(config), "optimized_test_sorter")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--auto-parallel",
        action="store_true",
        default=False,
        help="Automatically determine the optimal number of parallel processes based on CPU cores",
    )


def pytest_cmdline_main(config):
    """Set up parallel execution if requested."""
    if config.getoption("--auto-parallel"):
        import multiprocessing
        
        # Use CPU count - 1 for optimal performance, minimum of 2
        num_cpus = max(multiprocessing.cpu_count() - 1, 2)
        
        # Add xdist options to the command line
        config.option.numprocesses = num_cpus
