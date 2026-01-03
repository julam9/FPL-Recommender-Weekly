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
    avg_position_points = sum(position_points.values())/len(position_points) if position_points else 0 
    for pos, points in position_points.items():
        if points < avg_position_points*0.7: # points are 30% or more below the average 
            areas_for_improvement.append(f"Consider strengthening {pos} position")
        
        # Check overall performance vs expectation 
        if performance_ratio < 0.8: # points are 20% or more below the expectation
            areas_for_improvement.append("Team performed significantly below expectations")
        
    # Return evaluation metrics 
    return{
        'gameweek' : gameweek,
        'total_points' : total_points,
        'position_points' : position_points,
        'player_points' : player_points, 
        'expected_points' : expected_points, 
        'performance_ratio' : performance_ratio,
        'areas_for_improvement' : areas_for_improvement,
        'timestamp' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")        
    }
    
def record_performance(performance_data:Dict[str, Any], gameweek:int) -> None: 
    """
    Save performance data to a file 
    
    Args:
        performance_data : Dictionary containing performance data
        gameweek: Current gameweek number
    """ 
    
    # Ensure data directory exists 
    os.makedirs('data', exist_ok=True)
    
    # Save to a file 
    with open(f"data/performance_gw{gameweek}.json", 'w') as f:
        json.dump(performance_data, f, indent=4)
        
    # Update performance history file 
    update_performance_history(performance_data)
    
def update_performance_history(performance_data:Dict[str, Any]) -> None: 
    """
    Update the consolidated performance history file 
    
    Args: 
        performance_data: Dictionary containing performance data for a gameweek
    """
    
    # Ensure data directory exists 
    os.makedirs('data', exist_ok=True)
    
    history_file = 'data/performance_history.json'
    history=[]
    
    # Load existing history if available 
    if os.path.exists(history_file):
        try: 
            with open(history_file, 'r') as f: 
                history = json.loads(f)
        except: 
            history = []
            
    # Check if entry for this gameweek already exists 
    gameweek = performance_data['gameweek']
    existing_index=None 
    
    for i, entry in enumerate(history):
        if entry.get('gameweek') == gameweek:
            existing_index = i 
            break 
        
    # Update or append 
    if existing_index is not None:
        history[existing_index] = performance_data
    else:
        history.append(performance_data)
        
    # Save updated history 
    with open(history_file, 'w') as f: 
        json.dump(history, f, indent=4)
        
def get_performance_history() -> List[Dict[str, Any]]: 
    """ 
    Get performance history for all recorded gameweeks 
    
    Returns: 
        List of dictionaries containing performance data
    """
    
    history_file = 'data/performance_history.json' 
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f: 
                history = json.loads(f)
            return history
        except:
            return []
        
    return [] 

def get_team_form(gameweek:int, window: int=5) -> float:
    """ 
    Calculate team form based on recent performance 
    
    Args: 
        gameweek: Current gameweek number
        window : Number of gameweeks to consider for form evaluation
        
    Returns: 
        Form rating (0-10 scale)    
    """
    
    # Get performance history 
    history = get_performance_history() 
    
    # Filter to recent gameweeks 
    recent_gws = [gw for gw in history if gw['gameweek'] > gameweek - window and gw['gameweek'] < gameweek]
    
    if not recent_gws: 
        return 5.0  # Neutral form if no data
    
    # Calculate form based on performance ratio 
    form_sum = sum(gw.get('performance_ratio', 1.0) for gw in recent_gws)
    form = form_sum/len(recent_gws)*5 
    
    # Ensure form is within 0-10 range 
    form = max(0, min(10, form))
    
    return round(form, 1)

def analyze_performance_trends(num_gameweeks: int=5) -> Dict[str, Any]: 
    """
    Analyze trends in team performance over recent gameweeks
    
    Args: 
        num_gameweeks: Number of most recent gameweeks to analyze
    
    Returns:
        Dictionary containing performance trend analysis
    """
    
    # Get performance history 
    history = get_performance_history() 
    
    if not history:
        return {
            'trend' : 'Unknown',
            'avg_points' : 0,
            'point_trend': 'Stable',
            'best_positions': [],
            'worst_positions': [],
            'top_performers': []            
        }
    
    # Sort by gameweek in descending order 
    history.sort(key=lambda x: x['gameweek'], reverse=True)
    
    # Get most recent gameweeks 
    recent_gws = history[:num_gameweeks] if len(history) >= num_gameweeks else history 
    
    # Calculate average points 
    total_points = [gw.get('total_points', 0) for gw in recent_gws]
    avg_points = sum(total_points)/len(total_points) if total_points else 0 
    
    # Determine point trend 
    if len(total_points) >= 3:
        first_half = total_points[len(total_points)//2:]
        second_half = total_points[:len(total_points)//2]
        
        first_avg = sum(first_half)/len(first_half) if first_half else 0 
        second_avg = sum(second_half)/len(second_half) if second_half else 0 
        
        if second_avg > first_avg*1.1:
            point_trend = 'Improving'
        elif second_avg < first_avg*0.9: 
            point_trend = "Declining"
        else:
            point_trend = "Stable"
    else:
        point_trend = "Unknown"
        
    # Analyze positions 
    all_positions = {}
    
    for gw in recent_gws:
        if 'position_points' in gw:
            for pos, points in gw['position_points'].items(): 
                if pos not in all_positions:
                    all_positions[pos] = []
                all_positions[pos].append(points)
                
    # Calculate average points per position 
    pos_averages = {}
    for pos, points in all_positions.items():
        pos_averages[pos] = sum(points)/len(points)
        
    # Find best and worst positions
    sorted_positions = sorted(pos_averages.items(), key=lambda x:x[1], reverse=True)
    best_positions = [pos for pos, _ in sorted_positions[:3]] if len(sorted_positions) >= 3 else [pos for pos, _ in sorted_positions]
    worst_positions = [pos for pos, _ in sorted_positions[-3:]] if len(sorted_positions) >= 3 else [pos for pos, _ in sorted_positions]
    
    # Find top performing players 
    all_players = {}
    for gw in recent_gws: 
        if 'player_points' in gw:
            for player, points in gw['player_points'].items():
                if player not in all_players:
                    all_players[player] = []
                all_players[player].append(points)
                
    # Calculate average points per player 
    player_averages = {}
    for player, points in all_players.items():
        player_averages[player] = sum(points)/len(points)
        
    # Get top performers 
    top_performers = sorted(player_averages.items(), key=lambda x: x[1], reverse=True)[:5] 
    
    return { 
        'trend' : point_trend,
        'avg_points' : round(avg_points, 1),
        'point_trend' : point_trend,
        'best_positions' : best_positions,
        'worst_positions' : worst_positions,
        'top_performers' : top_performers   
    }