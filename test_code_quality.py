#!/usr/bin/env python3
"""
Test file for code quality module.
This file intentionally contains code quality issues to test the code quality module.
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional


def add_numbers(a, b):
    """Add two numbers together."""
    return a + b


def unused_function(x):
    """This function is never used."""
    return x * 2


class TestClass:
    """A test class with code quality issues."""

    def __init__(self, name):
        """Initialize the class."""
        self.name = name
        self.value = None

    def set_value(self, value):
        """Set the value."""
        self.value = value

    def get_value(self):
        """Get the value."""
        return self.value


# Old-style string formatting
message = "Hello, %s!" % "world"

# Unused variable
unused_var = 42

# List comprehension that could be simplified
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]

if __name__ == "__main__":
    # Create an instance of TestClass
    test = TestClass("test")
    test.set_value(10)

    # Print the result of add_numbers
    result = add_numbers(5, 10)
    print(f"Result: {result}")

    # Print the value from TestClass
    print(f"Value: {test.get_value()}")
