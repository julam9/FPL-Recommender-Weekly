"""
Test for the utils module to verify utility functions
"""

import unittest
import os 
import pandas as pd
from src.utils import (
    get_current_gameweek,
    convert_positions_to_formation,
    format_price,
    calculate_team_stats,
    export_team_to_csv 
)

class TestUtils(unittest.TestCase): 
    """Test cases for the utils module"""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create sample squad for testing
        self.test_squad = [
            {"name": "Player 1", "position": "GK", "price": 5.0, "performance_score": 75},
            {"name": "Player 2", "position": "DEF", "price": 6.5, "performance_score": 80},
            {"name": "Player 3", "position": "DEF", "price": 5.5, "performance_score": 78},
            {"name": "Player 4", "position": "DEF", "price": 5.0, "performance_score": 70},
            {"name": "Player 5", "position": "DEF", "price": 4.5, "performance_score": 65},
            {"name": "Player 6", "position": "MID", "price": 9.0, "performance_score": 85},
            {"name": "Player 7", "position": "MID", "price": 8.5, "performance_score": 82},
            {"name": "Player 8", "position": "MID", "price": 8.0, "performance_score": 80},
            {"name": "Player 9", "position": "MID", "price": 7.0, "performance_score": 75},
            {"name": "Player 10", "position": "FWD", "price": 12.0, "performance_score": 90},
            {"name": "Player 11", "position": "FWD", "price": 10.5, "performance_score": 85}  
        ]
        
        # Sample manager info 
        self.manager_info = {
            "name" : "Test Manager",
            "team_name" : "Test FC",
            "favorite_team" : "Team A"            
        }
        
    def test_convert_positions_to_formation(self):
        """Test formation string generation from position"""
        # Test with 4-4-2 formation
        formation = convert_positions_to_formation(self.test_squad)
        self.assertEqual(formation, "4-4-2")