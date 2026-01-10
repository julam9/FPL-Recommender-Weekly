""" 
Tests for the team_optimizer module to verify team optimization functionality
"""

import unittest 
import pandas as pd
from unittest.mock import patch, MagicMock
from src.team_optimizer import (
    build_optimal_team,
    select_subtitutes, 
    optimize_team_for_opponent
)

class TestTeamOptimizer(unittest.TestCase):
    """Test cases for the team optimizer module."""
    
    def setUp(self):
        """Set up test data before each test method"""
        # Create sample player data 
        self.player_data = pd.DataFrame({
            'id' : range(1, 21),
            'name' : [f'Player {i}' for i in range(1, 21)],
            'position': ['GK', 'GK', 'DEF', 'DEF', 'DEF', 'DEF', 'DEF', 'MID', 'MID', 'MID', 
                        'MID', 'MID', 'FWD', 'FWD', 'GK', 'DEF', 'DEF', 'MID', 'MID', 'FWD'],
            'team': ['Team A', 'Team B', 'Team A', 'Team B', 'Team C', 'Team D', 'Team E', 
                    'Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team A', 'Team B',
                    'Team C', 'Team F', 'Team G', 'Team F', 'Team G', 'Team C'],
            'price': [5.0, 4.5, 6.0, 5.5, 5.0, 4.5, 4.0, 9.0, 8.5, 8.0, 7.5, 7.0, 12.0, 11.5, 4.0, 4.2, 4.3, 6.5, 6.0, 10.0],
            'performance_score': [75, 70, 80, 75, 70, 65, 60, 85, 80, 75, 70, 65, 90, 85, 65, 62, 63, 72, 68, 82],
            'form': [7.5, 7.0, 8.0, 7.5, 7.0, 6.5, 6.0, 8.5, 8.0, 7.5, 7.0, 6.5, 9.0, 8.5, 6.5, 6.2, 6.3, 7.2, 6.8, 8.2],
        })

        # Create sample fixture data 
        self.fixture_data = pd.DataFrame({
            'fixture_id': range(1, 11),
            'home_team': ['Team A', 'Team C', 'Team E', 'Team G', 'Team I', 'Team B', 'Team D', 'Team F', 'Team H', 'Team J'],
            'away_team': ['Team B', 'Team D', 'Team F', 'Team H', 'Team J', 'Team A', 'Team C', 'Team E', 'Team G', 'Team I'],
            'gameweek': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]
        })
        
        # Create sample team data
        self.team_data = pd.DataFrame({
            'team_id': range(1, 11),
            'name': ['Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team F', 'Team G', 'Team H', 'Team I', 'Team J'],
            'strength': [85, 80, 75, 70, 65, 60, 55, 50, 45, 40],
            'home_advantage': [10, 9, 8, 7, 6, 10, 9, 8, 7, 6]
        })
        
        # Sample budget
        self.budget = 100.0
        
    def test_build_optimal_team(self):
        """Test the build_optimal_team function"""
        # Get optimal team with default weights 
        optimal_team = build_optimal_team(
            self.player_data,
            self.budget,
            performance_weight=0.7, 
            budget_weight=0.3
        )
        
        # Check that the returned value is a list of dictionaries
        self.assertIsInstance(optimal_team, list)
        self.assertTrue(all(isinstance(player, dict) for player in optimal_team)) 
        
        # Check that the team has the expected number of players by position 
        positions = [player.get('position') for player in optimal_team]
        self.assertEqual(positions.count('GK'), 1) # at least 1 goalkeeper
        self.assertEqual(positions.count('DEF') >= 3) # at least 3 defenders 
        self.assertEqual(positions.count('MID') >= 2) # at least 2 midfielders 
        self.assertEqual(positions.count('FWD') >= 1) # at least 1 forward
        
        # Check that the total cost is within budget 
        total_cost = sum(player.get('price', 0) for player in optimal_team)
        self.assertLessEqual(total_cost, self.budget)
        
    def test_select_subtitutes(self):
        """Test the select_subtitutes function."""
        # Create a starting XI (first 11 players from the dataset)
        starting_xi = [
            self.player_data.iloc[i].to_dict() for i in range(11)
        ]        
        
        # Available players are the remaining players
        available_players = self.player_data.iloc[11:].copy()
        
        # Budget for substitutes
        sub_budget = 29.0
        
        # Select substitutes
        subs = select_subtitutes(
            available_players,
            sub_budget,
            current_squad=starting_xi
        )
        
        # Check that the returned value is a list of dictionaries
        self.assertIsInstance(subs, list)
        self.assertTrue(all(isinstance(player, dict) for player in subs))
        
        # Check that we have at most 4 substitutes 
        self.assertLessEqual(len(subs), 4)
        
        # Check that the total cost is within budget 
        total_cost = sum(player.get('price', 0) for player in subs)
        self.assertLessEqual(total_cost, sub_budget) 
        
    def test_optimize_team_for_opponent(self):
        """Test the optimize_team_for_opponent function"""
        # Create a current squad (15 players)
        current_squad = [
            self.player_data.iloc[i].to_dict() for i in range(15)
        ]
        
        # Opponent_team 
        opponent_team = "Team B"
        
        # Optimize starting lineup
        optimized_xi = optimize_team_for_opponent(
            current_squad,
            opponent_team,
            self.fixture_data,
            self.team_data
        )
        
        # Check that the returned value is a list of dictionaries
        self.assertIsInstance(optimized_xi, list)
        self.assertTrue(all(isinstance(player, dict) for player in optimized_xi))
        
        # Check that we have 11 players in the starting lineup
        self.assertEqual(len(optimized_xi), 11)
        
        # Check that we have appropriate positions 
        positions = [player.get('position') for player in optimized_xi]
        self.assertEqual(positions.count('GK'), 1) 
        self.assertEqual(positions.count('DEF') >= 3)
        self.assertEqual(positions.count('MID') >= 2)
        self.assertEqual(positions.count('FWD') >= 1)
        
if __name__ == "__main__":
    unittest.main()
        
        
        
        