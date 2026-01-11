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
        
        # Test with a 3-5-2 formation 
        squad_352 = self.test_squad.copy()
        squad_352[3]['position'] = 'MID'
        formation = convert_positions_to_formation(squad_352)
        self.assertEqual(formation, "3-5-2")
        
        # Test with a 4-3-3 formation
        squad_433 = self.test_squad.copy()
        squad_433[8]['position'] = 'FWD'
        formation = convert_positions_to_formation(squad_433)
        self.assertEqual(formation, "4-3-3")
    
    def test_format_price(self):
        """Test price formatting function"""
        
        # Test standard prices 
        self.assertEqual(format_price(5.0), "£5.0m")
        self.assertEqual(format_price(12.5), "£12.5m")
        
        # Test edge cases 
        self.assertEqual(format_price(0), "£0.0m")
        self.assertEqual(format_price(100), "£100.0m")
        
    def test_calculate_team_stats(self):
        """Test team statistics calculation"""
        stats = calculate_team_stats(self.test_squad)
        
        # Check that the stats dictionary contains expected keys 
        self.assertIn("total_value", stats)
        self.assertIn("average_performance", stats)
        self.assertIn("formation", stats)
        self.assertIn("position_counts", stats)
        
        # Verify total value calculation
        expected_value = sum(player['price'] for player in self.test_squad)
        self.assertEqual(stats['total_value'], expected_value)
        
        # Verify average performance calculation
        expected_avg = sum(player['performance_score'] for player in self.test_squad)/len(self.test_squad)
        self.assertEqual(stats['average_performance'], expected_avg)
        
        # Verify formation
        self.assertEqual(stats['formation'], '4-4-2')
        
        # Verify position counts
        self.assertEqual(stats['position_counts']['GK'], 1) 
        self.assertEqual(stats['position_counts']['DEF'], 4)
        self.assertEqual(stats['position_counts']['MID'], 4)
        self.assertEqual(stats['position_counts']['FWD'], 2)
        
    def test_export_team_to_csv(self):
        """Test team export to CSV functionality"""
        # Export team to CSV
        csv_path = export_team_to_csv(self.test_squad, self.manager_info)
        
        # Verify that the file was created 
        self.assertTrue(os.path.exists(csv_path))
        
        # Verify that the content is correct by loading it back
        try:
            df = pd.read_csv(csv_path)
            self.assertEqual(len(df), len(self.test_squad))
        
            # Check all the players are included
            player_names = df['name'].tolist()
            for player in self.test_squad:
                self.assertIn(player['name'], player_names)
            
            # Clean up the test file 
            if os.path.exists(csv_path):
                os.remove(csv_path) 
        
        except Exception as e:
            # Clean up the test file even if test fails
            if os.path.exists(csv_path):
                os.remove(csv_path)
            raise e

if __name__ == "__main__":
    unittest.main()        