"""
Tests for the player_evaluation module to verify player performance evaluation logic
"""
    
import unittest 
import pandas as pd
import numpy as np
from src.player_evaluation import (
    calculate_player_performance,
    calculate_position_weighted_score,
    calculate_form_trend,
    rank_players_by_position,
    get_position_specific_metrics,
    calculate_player_value    
)

class TestPlayerEvaluation(unittest.TestCase):
    """Test cases for the player evaluation module."""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create sample player data for testing
        self.player_data = pd.DataFrame({
            'id' : [1, 2, 3, 4, 5],
            'name' : ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5'],
            'position' : ['GK', 'DEF', 'MID', 'FWD', 'DEF'],
            'team' : ['Team A', 'Team B', "Team A", 'Team C', 'Team B'],
            'price' : [5.0, 6.5, 8.0, 10.5, 4.5],
            'total_points' : [75, 80, 85, 90, 70],
            'minutes_played' : [900, 850, 950, 800, 700],
            'goals_scored' : [0, 1, 5, 8, 0],
            'assists' : [0, 2, 6, 3, 1],
            'clean_sheets' : [4, 3, 1, 0, 2],
            'goals_concede' : [3, 5, 0, 0, 6],
            'saves' : [15, 0, 0, 0, 0],
            'yellow_cards' : [1, 2, 3, 2, 1],
            'red_cards' : [0, 0, 0, 1, 0],
            'form' : [7.5, 6.8, 8.2, 7.9, 6.5],
            'performance_score' : [75, 80, 85, 90, 70]
        })
        
        # Create sample performance history data 
        self.gameweek = 10 
        self.performance_history = pd.DataFrame({
            'player_id' : [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'gameweek' : [7, 8, 9, 7, 8, 9, 7, 8, 9],
            'points' : [6, 9, 8, 2, 5, 7, 12, 9, 10]            
        })
        
    def test_get_position_specific_metrics(self):
        """Test retrieving position-specific metrics"""
        gk_metrics = get_position_specific_metrics('GK')
        def_metrics = get_position_specific_metrics('DEF')
        mid_metrics = get_position_specific_metrics('MID')
        fwd_metrics = get_position_specific_metrics('FWD')
        
        # Verify that each position has its own set of metrics
        self.assertIn('saves', gk_metrics)
        self.assertIn('clean_sheets', def_metrics)
        self.assertIn('assists', mid_metrics)
        self.assertIn('goals_scored', fwd_metrics)
        
        # Verify that positions have appropriate metrics 
        self.assertIn('clean_sheets', gk_metrics)
        self.assertIn('goals_conceded', def_metrics)
        self.assertIn('saves', fwd_metrics)
        
    def test_calculate_player_value(self):
        """Test player value calculation based on performance and price"""
        # Test with a single player Series
        player = self.player_data.iloc[2] # Player  (MID)
        value = calculate_player_value(player)
        expected = player['performance_score']/player['price']
        self.assertAlmostEqual(value, expected)
        
    def test_rank_players_by_position(self):
        """Test ranking players within a position group"""
        # Filter for defenders 
        defenders = self.player_data[self.player_data['position'] == 'DEF']
        
        # Rank defenders 
        ranked = rank_players_by_position(defenders, self.gameweek)
        
        # Verify that ranking produces a DataFrame with the same number of rows 
        self.assertEqual(len(ranked), len(defenders))
        
        # Verify that ranking adds a 'rank' column
        self.assertIn('rank', ranked.columns)
        
        # Verify that the highest performance score has rank 1 
        best_player_idx = ranked['performance_score'].idmax()
        self.assertEqual(ranked.loc[best_player_idx, 'rank'], 1)
        
if __name__ = "__main__":
    unittest.main()