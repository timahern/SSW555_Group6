# Test utilities for standardized logging across all tests
# Usage:
#   from tests import TestLogger
#   with TestLogger("description of what is being tested"):
#       self.assertEqual(...)
# This will print a [TEST] line when starting, and [PASS]/[FAIL]/[ERROR] when finished.

class TestLogger:
    def __init__(self, description: str):
        self.description = description

    def __enter__(self):
        print(f"[TEST] {self.description}")
        return self

    def __exit__(self, exc_type, exc, tb):
        # If no exception, test block passed
        if exc_type is None:
            print(f"[PASS] {self.description}")
            return False  # don't suppress
        # If assertion failure, report FAIL and re-raise
        if issubclass(exc_type, AssertionError):
            print(f"[FAIL] {self.description}: {exc}")
            return False
        # Any other unexpected error
        print(f"[ERROR] {self.description}: {exc}")
        return False
