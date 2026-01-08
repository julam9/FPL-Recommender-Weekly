"""
Tests for the opponent_analyzer module to verify opponent analysis functionality.
""" 

import unittest 
import pandas as pd 
from src.opponent_analyzer import (
    get_opponent_strength, 
    adjust_score_for_opponent,
    calculate_fixture_difficulty_rating,
    get_fixture_difficulty_rating    
)

class TestOpponentAnalyzer(unittest.TestCase): 
    """Test cases for the opponent analyzer module."""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create sample fixture data
        self.fixture_df = pd.DataFrame({
            'gameweek' : [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'home_team' : ['Team A', 'Team C'. 'Team E', 'Team B', 'Team D', 'Team F', 'Team A', 'Team C', 'Team E']
            'away_team' : ['Team B', 'Team D', 'Team F', 'Team A', 'Team C', 'Team E', 'Team D', 'Team F', 'Team B']
        })
        
        # Create sample team data
        self.teams_df = pd.DataFrame({
            'name' : ['Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team F'],
            'strength' : [85, 80, 75, 70, 65, 60],
            'home_advantage' : [10, 9, 8, 7, 6, 5]
        })
        
        # Current gameweek for testing 
        self.current_gameweek = 2 
        
    def test_get_opponent_strength(self):
        """Test the get_opponent_strength function"""
        # Test for a team with a fixture in the current gameweek 
        team_a_opponent = get_opponent_strength('Team A', self.current_gameweek, self.fixtures_df, self.teams_df)
        
        # Verify the opponent information is correct 
        self.assertIsNotNone(team_a_opponent)
        self.assertEqual(team_a_opponent['opponent'], 'Team B')
        self.assertEqual(team_a_opponent['is_home'], False)
        self.assertEqual(team_a_opponent['opponent_strength'], 80)
        
        # Test for a team with no fixture in the current gameweek 
        nonexistent_team = get_opponent_strength('Team Z', self.current_gameweek, self.fixturest_df, self.teams_df)
        self.assertIsNone(nonexistent_team)
        
    def test_adjust_score_for_opponent(self): 
        """Test score adjustment based on opponent strength"""
        # Test with a strong opponent, away game 
        base_score = 75.0
        opponent_strength = 85.0 
        is_home = True 
        
        adjsuted_score = adjust_score_for_opponent(base_score, opponent_strength, is_home)
        
        # Expect score to be increased against weak opponent at home 
        self.assertGreater(adjusted_score, base_score)  
        
    def test_calculate_fixture_difficulty_rating(self):
        """Test fixture difficulty rating calculation"""
        # Test for a team playing against a strong opponent away 
        fdr = calculate_fixture_difficulty_rating('Team A', 'Team F', False, self.teams_df)
        
        # Verify FDR is higher (more difficult) when playing a strong team away 
        self.assertGreater(fdr, 3.0)
        
        # Test for a team playing against a weak opponent at home 
        fdr = calculate_fixture_difficulty_rating('Team A', 'Team F', True, self.teams_df)
        
        
        # Verify FDR is lower (less difficult) when playing weak team at home
        self.assertLess(fdr, 3.0)
        
    def test_get_fixture_difficulty_trend(self):
        """Test fixture trend for next 3 gameweeks"""
        team = 'Team A
        num_gameweeks = 3 
        
        trend = get_fixture_difficulty_trend(
            team, 
            self.current_gameweek,
            num_gameweeks,
            self.fixtures_df,
            self.teams_df
        )
        
        # Verify the trend information
        self.assertIsInstance(trend, dict)
        self.assertIn('fixtures', trend)
        self.assertIn('average_difficulty', trend)
        self.assertIn('difficulty_trend', trend)
        
        # Verify that the right number of fixtures are returned
        self.assertLessEqual(len(trend['fixtures']), num_gameweeks)
        
        # Verify that the average difficulty is a float between 1 and 5
        self.assertGreaterEqual(trend['average_difficulty'], 1.0)
        self.assertLessEqual(trend['average_difficulty'], 5.0)

if __name__ == "__main__":
    unittest.main()        

















