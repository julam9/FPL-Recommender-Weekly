import pandas as pd
import numpy as np 
from typing import Dict, List 

def calculate_player_performance(player_data:pd.DataFrame, gameweek:int) -> pd.DataFrame: 
    """
    Calculate performance scores for players based on various metrics
    
    Args:
        player_data : DataFrame containing player information 
        gameweek : Current gameweek number

    Returns:
        DataFrame with updated performance scores
    """
    # Create a copy of the input data 
    players_df = player_data.copy()
    
    # Apply position-specific scoring weights 
    players_df['weighted_score'] = players_df.apply(
        lambda x: calculate_position_weighted_score(x, gameweek),
        axis=1
    )
    
    # Update form based on recent performances (trending up or down)
    players_df['form_trend'] = players_df.apply(
        lambda x: calculate_form_trend(x, gameweek),
        axis=1
    )
    
    # Adjust performance score based on form trend
    players_df['performance_score'] = players_df['weighted_score']*(1+(players_df['form_trend']*0.1))
    
    # Ensure scores are within reasonable bounds 
    players_df['performance_score'] = players_df['performance_score'].clip(0, 100)
    
    return players_df 

def calculate_position_weighted_score(player: pd.Series, gameweek:int) -> float:
    """
    Calculate weighted performance score based on player position
    
    Args:
        player: Player data as pandas Series 
        gameweek: Current gameweek number
    
    Returns:
        Weighted performance score    
    """
    
    position = player['position']
    base_score = player['performance_score']
    
    # Define position-specific weights 
    weights = {
        'GK': {
            'clean_sheets' : 4.0, 
            'goals_conceded': -0.5,
            'saves': 0.25, 
            'minutes_played' : 0.02            
        }, 
        'CB': {
            'clean_sheets' : 4.0,
            'goals' : 6.0,
            'assists' : 3.0,
            'goals_conceded' : -0.5,
            'minutes_played' : 0.02            
        },
        'RB': {
            'clean_sheets' : 4.0,
            'goals' : 6.0,
            'assists' : 3.0,
            'goals_conceded': -0.5,
            'key_passes': 0.5,
            'minutes_played' : 0.02            
        },
        'LB': {
            'clean_sheets' : 4.0,
            'goals': 6.0,
            'assists': 3.0,
            'goals_conceded': -0.5,
            'key_passes': 0.5,
            'minutes_played': 0.02    
        },
        'DM': {
            'clean_sheets' : 1.0,
            'goals': 6.0,
            'assists': 3.0,
            'key_passes': 0.5,
            'minutes_played': 0.02         
        },
        'CM': {
            'goals': 5.0,
            'assists': 3.0,
            'key_passes': 0.5,
            'minutes_played': 0.02         
        }
        
        
               
        
        
        
    }