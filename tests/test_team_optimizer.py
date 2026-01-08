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
        