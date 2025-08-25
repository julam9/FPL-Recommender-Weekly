import pandas as pd
from typing import Dict, List, Any
import os
from datetime import datetime 

# Define position requirements for starting XI
positions_required = {
    'GK': 1,
    'RB': 1,
    'CB': 2,
    'LB': 1,
    'DM': 1,
    'CM': 1,
    'AM': 1,
    'RW': 1,
    'ST': 1,
    'LW': 1
}
 
# Define total squad requirements (including starting XI and subs)
total_squad_requirements = {
    'GK': 3,    # 3 goalkeepers
    'DEF': 5,   # 5 defenders (RB, CB, LB)
    'MID': 5,   # 5 midfielders (DM, CM, AM)
    'FWD': 2    # 2 forwards (RW, ST, LW)
}

def get_current_gameweek() -> int:
    """
    Determine current gameweek based on saved data or default to first gameweek
    
    Returns:
        Current gameweek number
    """
    # Check if we have performance history
    if os.path.exists('data/performance_history.json'):
        import json
        try:
            with open('data/performance_history.json', 'r') as f:
                history = json.load(f)
                
            if history:
                # Find the maximum gameweek in history
                max_gameweek = max(entry.get('gameweek', 0) for entry in history)
                # The current gameweek is the next one
                return max_gameweek + 1
        except:
            pass

        # If we have squad data, find the latest gameweek
    data_files = [f for f in os.listdir('data') if f.startswith('squad_gw') and f.endswith('.json')]
    
    if data_files:
        gameweeks = []
        for file in data_files:
            try:
                gw = int(file.replace('squad_gw', '').replace('.json', ''))
                gameweeks.append(gw)
            except:
                pass
        
        if gameweeks:
            return max(gameweeks) + 1
    
    # Default to first gameweek
    return 1
 
def convert_positions_to_formation(starting_xi: List[Dict[str, Any]]) -> str:
    """
    Convert starting XI positions to formation string (e.g., 4-3-3)
    
    Args:
        starting_xi: List of player dictionaries in the starting XI
        
    Returns:
        Formation string
    """
    if not starting_xi:
        return "Unknown"
    
    # Count players in each role
    defenders = sum(1 for player in starting_xi if player['position'] in ['RB', 'CB', 'LB'])
    midfielders = sum(1 for player in starting_xi if player['position'] in ['DM', 'CM', 'AM'])
    forwards = sum(1 for player in starting_xi if player['position'] in ['RW', 'ST', 'LW'])
    
    return f"{defenders}-{midfielders}-{forwards}" 

def format_price(price: float) -> str:
    """
    Format price value to string with million symbol
    
    Args:
        price: Price value
        
    Returns:
        Formatted price string
    """
    return f"£{price:.1f}M" 

def calculate_team_stats(squad: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate various team statistics
    
    Args:
        squad: List of player dictionaries in the squad
        
    Returns:
        Dictionary containing team statistics
    """
    if not squad:
        return {
            'avg_price': 0,
            'avg_performance': 0,
            'formation': "Unknown",
            'team_diversity': 0
        }
    
    # Calculate average price and performance
    avg_price = sum(player['price'] for player in squad) / len(squad)
    avg_performance = sum(player['performance_score'] for player in squad) / len(squad)
    
    # Calculate formation
    starting_xi = squad[:11] if len(squad) >= 11 else squad
    formation = convert_positions_to_formation(starting_xi)
    
    # Calculate team diversity (number of different teams)
    teams = set(player['team'] for player in squad)
    team_diversity = len(teams)
    
    return {
        'avg_price': round(avg_price, 1),
        'avg_performance': round(avg_performance, 1),
        'formation': formation,
        'team_diversity': team_diversity
    }
