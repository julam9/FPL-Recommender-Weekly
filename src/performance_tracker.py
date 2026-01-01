import pandas as pd
import json
import os 
from datetime import datetime 
from typing import Dict, Any, List 


def evaluate_team_performance(
    selected_squad: List[Dict[str, Any]],
    actual_points: Dict[str, int],
    gameweek: int
) -> Dict[str, Any]: 
    """
    
    Evaluate team performance based on actual points scored
    
    Args:
        selected_squad : List of player dictionaries in the selected squad 
        actual_points : Dictionary mapping player names to actual points 
        gameweek (int): Current gameweek

    Returns:
        Dictionary containing performance evaluation metrics
    """
    
    # Calculate total points 
    total_points = sum(actual_points.values()) 
    
    #Calculate points by position 
    position_points = {}
    player_points = {}
    
    for player in selected_squad: 
        name = player['name']
        position = player['position']
        
        # Add positions to position_points dict if not exists
        if position not in position_points: 
            position_points[position] = 0 
            
        # Get actual points for the player 
        points = actual_points.get(name, 0)
        
        # Add to position total
        position_points[position] += points 
        
        # Store individual player points 
        player_points[name] = points 
        
    # Calculate expected points based on performance scores 
    expected_points = sum([player['performance_score']/2 for player in selected_squad])
    
    # Calculate performance vs expectation
    performance_ratio = total_points / expected_points if expected_points > 0 else 0 
    
    # Determine areas for improvement
    areas_for_improvement = {}
    
    # Check for underperforming positions