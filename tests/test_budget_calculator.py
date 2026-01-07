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
        
    def test_calculate_squad_values(self):
        """Test the calculate_squad_value function"""
        squad_value = calculate_squad_value(self.test_squad)
        expected = sum(player['price'] for player in self.test_squad)
        self.assertEqual(squad_value, expected)
        
    def test_calculate_player_value(self):
        """Test the calculate_player_value function for a single player"""
        player = self.test_squad[2] # Third player with position MID 
        value = calculate_player_value(player)
        expected = player['performance_score']/player['price']
        self.assertEqual(value, expected)

    def test_calculate_budget_allocation(self):
        """Test the budget allocation calculation by position""" 
        allocation = calculate_budget_allocation(self.test_squad)
        total_budget_used = sum(player['price'] for player in self.test_squad) 
        
        # Calculate expected allocations manually 
        gk_allocation = sum(player['price'] for player in self.test_squad if player['position'] == 'GK')/total_budget_used*100
        def_allocation = sum(player['price'] for player in self.test_squad if player['position'] == 'DEF')/total_budget_used*100
        mid_allocation = sum(player['price'] for player in self.test_squad if player['position'] == 'MID')/total_budget_used*100
        fwd_allocation = sum(player['price'] for player in self.test_squad if player['position'] == 'FWD')/total_budget_used*100
        
        self.assertEqual(allocation['GK'], gk_allocation)
        self.assertEqual(allocation['DEF'], def_allocation)
        self.assertEqual(allocation['MID'], mid_allocation)
        self.assertEqual(allocation['FWD'], fwd_allocation)
        
    def test_calculate_budget_efficiency(self):
        """Test budget efficiency metrics calculation"""
        efficiency = calculate_budget_efficiency(self.test_squad)
        
        # Verify the efficiency metrics 
        self.assertIn("average_value", efficiency)
        self.assertIn('best_value_player', efficiency)
        self.assertIn('position_values', efficiency)
        
        # Calculate expected average value
        expected_avg_value = sum(player['performance']/player['price'] for player in self.test_squad)/len(self.test_squad)
        self.assertAlmostEqual(efficiency['average_value'], expected_avg_value) 
        
        # Verify best value player is the one with highest performance per million
        best_value = max(self.test_squad, key=lambda p:p['performance_score']/p['price'])
        self.assertEqual(efficiency['best_value_player']['name'], best_value['name'])

if __name__ = "__main__":
    unittest.main()