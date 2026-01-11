#!/usr/bin/env python
"""      
Test runner script for the Football Team Recommendation System
Run this script to execute all unit tests
"""

import sys
import os
import unittest 

def run_tests():
    """
    Discover and run all tests in the tests directory
    """
    
    # Add the /src directory to the Python path 
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
    
    # Find the tests directory 
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
    
    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover(test_dir, pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test results 
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())