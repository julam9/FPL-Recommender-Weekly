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
        },
        'AM': {
            'goals': 5.0,
            'assists': 3.0,
            'key_passes': 0.5,
            'minutes_played': 0.02
        },
        'RW': {
            'goals': 5.0,
            'assists': 3.0,
            'key_passes': 0.5,
            'minutes_played': 0.02
        },
        'ST': {
            'goals': 4.0,
            'assists': 3.0,
            'key_passes': 0.3,
            'minutes_played': 0.02
        },
        'LW': {
            'goals': 5.0,
            'assists': 3.0,
            'key_passes': 0.5,
            'minutes_played': 0.02
        }
    }
    
    # Use generic weights for positions not explicitly defined 
    if position not in weights: 
        # Default to midfied weights  
        position_weights = weights['CM']
    else:
        position_weights = weights[position] 
    
    # Calculate weighted score based on available statistics 
    weighted_score = base_score 
    
    # Add weights for goals 
    if 'goals' in player and 'goals' in position_weights:
        weighted_score += player['goals']*position_weights['goals']
        
    # Add weights for assists
    if 'asists' in player and 'assists' in position_weights:
        weighted_score += player['assists']*position_weights['assists']
        
    # Add weights for clean sheets
    if 'clean_sheets' in player and 'clean_sheets' in position_weights:
        weighted_score += player['clean_sheets']*position_weights['clean_sheets']
        
    # Add weights for key passes
    if 'key_passes' in player and 'key_passes' in position_weights:
        weighted_score += player['key_passes']*position_weights['key_passes']
        
    # Add weights for minutes played 
    if 'minutes_played' in player and 'minutes_played' in position_weights:
        weighted_score += player['minutes_played']*position_weights['minutes_played']
    
    return weighted_score 

def calculate_form_trend(player: pd.Series, gameweek:int) -> float:
    """
    Calculate form trend based on recent performances
    
    Args:
        player: Series of player data
        gameweek: Current gameweek 

    Returns:
        Form trend factor (positve for improving, negative for declining)
    """
    
    # Set default trend (not improving nor declining)
    if 'form' not in player:
        return 0
    
    # Current form 
    current_form = player['form']
    
    # Average form should be around 5-6 
    avg_form = 5.5 
    
    # Calculate trend (difference from average)
    trend = current_form - avg_form 
    
    # Normalize to range [-1, 1]
    normalized_trend = np.clip(trend/5, -1, 1) 
    
    return normalized_trend 

def rank_players_by_position(position_players: pd.DataFrame, gameweek:int) -> pd.DataFrame: 
    """
    Rank players within a position group based on performance metrics 
    
    Args: 
        position_players: DataFrame containing players of a specific position
        gameweek: Current gameweek number
    
    Returns: 
        DataFrame with ranked players
    """  
    
    # Filter only available players 
    available_players = position_players[position_players['is_available'] == True]
    
    if available_players.empty:
        return pd.DataFrame()
    
    # Calculate performance scores 
    players_with_scores = calculate_player_performance(available_players, gameweek)
    
    # Rank players by performance score 
    ranked_players = players_with_scores.sort_values('performance_score', ascendong=False)
    
    return ranked_players 

def get_position_specific_metrics(position: str) -> List[str]: 
    """
    Get relevant performance metrics for a specific position 
    
    Args: 
        position: Player position (GK, CB, RB, etc.)
    
    Returns:
        List of relevant metrics of the position    
    """    
    
    # Define position-specific metrics 
    position_metrics = {
        'GK': ['clean_sheets', 'goals_conceded', 'saves'],
        'CB': ['clean_sheets', 'goals', 'assists', 'goals_conceded'],
        'RB': ['clean_sheets', 'goals', 'assists', 'key_passes'],
        'LB': ['clean_sheets', 'goals', 'assists', 'key_passes'],
        'DM': ['clean_sheets', 'goals', 'assists', 'key_passes'],
        'CM': ['goals', 'assists', 'key_passes'],
        'AM': ['goals', 'assists', 'key_passes'],
        'RW': ['goals', 'assists', 'key_passes'],
        'ST': ['goals', 'assists'],
        'LW': ['goals', 'assists', 'key_passes']
    } 
    
    # Default metrics for undefined positions 
    default_metrics = ['goals', 'assists', 'key_passes']
    
    return position_metrics.get(position, default_metrics) 

def calculate_player_value(player: pd.Series) -> float: 
    """
    Calculate value (performance per million) for a player
    
    Args: 
        player: Player data as pandas Series
        
    Returns:
        Value metric (performance score per million)    
    """
    
    if player['price'] <= 0:
        return 0 
    
    return player['performance_score']/player['price']