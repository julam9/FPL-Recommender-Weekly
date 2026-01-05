"""
Tests for the budget_calculator module to verify budget calculation functionality    
"""

import unittest 
import pandas as pd 
from src.budget_calculator import (
    calculate_remaining_budget,
    calculate_squad_value,
    calculate_player_value,
    calculate_budget_allocation,
    calculate_budget_efficiency
) 

class TestBudgetCalculator(unittest.TestCase):
    """ Test case for the budget calculator module."""
    
    def setUp(self): 
        """Set up test data before each test method."""
        self.test_squad = [
            {"name" : "Player 1", "position" : "GK", "price" : 5.0, "performance_score" : 75},
            {"name" : "Player 2", "position" : "DEF", "price" : 6.5, "performance_score" : 80},
            {"name" : "Player 3", "position" : "MID", "price" : 8.0, "performance_score" : 85},
            {"name" : "Player 4", "position" : "FWD", "price" : 10.5, "performance_score" : 90},
            {"name" : "Player 5", "position" : "DEF", "price" : 4.5, "performance_score" : 70}
        ]
        self.total_budget = 100.0
        
    def test_calculate_remaining_budget(self): 
        """Test the calculate_remaining_budget function"""
        remaining = calculate_remaining_budget(self.test_squad, self.total_budget)
        expected = self.total_budget - sum(player['price'] for player in self.test_squad)
        self.assertEqual(remaining, expected)