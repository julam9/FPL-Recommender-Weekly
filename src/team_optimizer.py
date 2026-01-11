import pandas as pd 
import numpy as np 
from typing import Dict, List, Any 

from player_evaluation import calculate_player_value, rank_players_by_position 
from opponent_analyzer import adjust_score_for_opponent 
from utils import positions_required, total_squad_requirements 

def build_optimal_team(
    players_df: pd.DataFrame,
    budget: float, 
    performance_weight: float=0.7, 
    budget_weight: float=0.3,
    consider_opponents: bool=True,
    next_opponents: Dict=None,
    prioritize_form: bool=True    
) -> List[Dict[str, Any]]: 
    """
    Build an optimal starting XI based on performance, budget, and opponent strength
    
    Args:
        players_df: DataFrame containing all players
        budget: Available budget for starting XI 
        performance_weight: Weight given to performance (0-1) 
        budget_weight: Weight given to budget efficiency (0-1)
        consider_opponents: Whether to consider opponent strength 
        next_opponents: Dictionary mapping teams to their next opponents 
        prioritize_form: Whether to prioritize current form over season-long performance.

    Returns:
        List of dictionaries containing selected players for starting XI
    """
    
    # Validate weights 
    if performance_weight + budget_weight != 1.0:
        # Normalize weights 
        total = performance_weight + budget_weight 
        performance_weight /= total 
        budget_weight /= total 
        
    # Filter only available players 
    available_players = players_df[players_df['is_available'] == True].copy() 
    
    # Calculate player value 
    available_players['value'] = available_players.apply(calculate_player_value, axis=1) 
    
    # Adjust scores for opponent strength if requested
    if consider_opponents and next_opponents: 
        for idx, player in available_players.iterrows(): 
            team = player['team']
            if team in next_opponents:
                opponent_info = next_opponents[team]
                adjusted_score = adjust_score_for_opponent( 
                        player['performance_score'],
                        opponent_info['strength'],
                        opponent_info['is_home']       
                        )
                available_players.loc[idx, 'adjusted_score'] = adjusted_score 
            else:
                available_players.loc[idx, 'adjusted_score'] = player['performance_score']
    else:
        available_players['adjusted_score'] = available_players['performance_score']
        
    # Prioritize form if requested 
    if prioritize_form:  
        # Blend current form with performance score 
        available_players['blended_score'] = (
            available_players['adjusted_score']*0.7 + 
            (available_players['form']*10)*0.3            
        )
    else: 
        available_players['blended_score'] = available_players['adjusted_score']
        
    # Calculate composite score based on weights 
    available_players['composite_score'] = (
        available_players['blended_score']*performance_weight + 
        available_players['value']*10*budget_weight # Scale value to match the performance score range
    )
    
    # Initialize selected players list and remaining budget 
    selected_players = []
    remaining_budget = budget 
    
    # Select players for each required position 
    for position, count in positions_required.items():
        # Skip subtitute positions 
        if position in ['SUB GK', 'SUB DEF', 'SUB MID', 'SUB FWD']:
            continue
        
        # Filter players for this position 
        position_players = available_players[available_players['position']==position]
        
        # Skip if no players available for this position 
        if position_players.empty:
            continue 
        
        # Sort by composite score 
        position_players = position_players.sort_values(by='composite_score', ascending=False)
        
        # Select the required number of players for this position 
        for i in range(count): 
            if i < len(position_players): 
                # Get the player with highest composite score that fits the budget 
                affordable_players = position_players[position_players['price']<=remaining_budget]
                
                if affordable_players.empty: 
                    # No affordable players found, try to find cheaper alternative
                    continue 
                
                selected_player = affordable_players.iloc[0]
                
                # Add to selected players 
                player_dict = {
                    'player_id' : selected_player['player_id'],
                    'name' : selected_player['name'],
                    'position' : selected_player['position'],
                    'team': selected_player['team'],
                    'price': selected_player['price'],
                    'performance_score': selected_player['performance_score'],
                    'form': selected_player['form']
                }
                selected_players.append(player_dict)
                
                # Update remaining budget 
                remaining_budget -= selected_player['price']
                
                # Remove selected player from available players 
                available_players = available_players[available_players['player_id'] != selected_player['player_id']]
                position_players = position_players[position_players['player_id'] != selected_player['player_id']]
                
    return selected_players

def select_substitutes( 
    available_players: pd.DataFrame,
    budget: float, 
    current_squad: List[Dict[str, Any]] = None, 
    performance_weight: float = 0.5, 
    budget_weight: float = 0.5   
) -> List[Dict[str, Any]]: 
    """
    Select subtitutes based on available players and budget
    
    Args:
        available_players: DataFrame containing available players (excluding starting XI)
        budget : Available budget for subtitutes
        current_squad (List[Dict[str, Any]], optional): _description_. Defaults to None.
        performance_weight (float, optional): _description_. Defaults to 0.5.
        budget_weight (float, optional): _description_. Defaults to 0.5.

    Returns:
        List[Dict[str, Any]]: _description_
    """
    if current_squad is None: 
        current_squad = []
    
    # Calculate required substitute positions based on total requirements 
    sub_positions = {
        'GK': total_squad_requirements['GK'] - sum(1 for p in current_squad if p['position']=='GK'),
        'DEF': total_squad_requirements['DEF'] - sum(1 for p in current_squad if p['position'] in ['RB', 'CB', 'LB']),
        'MID': total_squad_requirements['MID'] - sum(1 for p in current_squad if p['position'] in ['DM', 'CM', 'AM']),
        'FWD': total_squad_requirements['FWD'] - sum(1 for p in current_squad if p['position'] in ['ST', 'RW', 'LW']),
    }
    
    # Mapping from player positions to subtitute categories 
    position_mapping = {
        'GK' : 'GK',
        'CB' : 'DEF',
        'RB' : 'DEF',
        'LB' : 'DEF',
        'DM' : 'MID',
        'CM' : 'MID',
        'AM' : 'MID',
        'ST' : 'FWD',
        'RW' : 'FWD',
        'LW' : 'FWD'        
    }
    
    # Validate weights 
    if performance_weight + budget_weight != 1.0:
        # Normalize weights 
        total = performance_weight + budget_weight 
        performance_weight /= total 
        budget_weight /= total 
    
    # Calculate player value 
    available_players['value'] = available_players.apply(calculate_player_value, axis=1)
    
    # Calculate composite score based on weights
    available_players['composite_score'] = (
        available_players['performance_score'] * performance_weight + available_players['value']*10*budget_weight # Scale value to be comparable to performance score
    )
    
    # Initialize selected subtitutes and remaining budget 
    selected_subs = []
    remaining_budget = budget
    
    # Select players for each subtitute category 
    for sub_category, count in sub_positions.items():
        # Filter players for this substitute category 
        category_players = available_players[available_players['position'].apply(lambda x:position_mapping.get(x) == sub_category)]
    
    # Skip if not players available for this category 
        if category_players.empty:
            continue
        
    # Sort by composite score
    category_players = category_players.sort_values('composite_score', ascending=False)
    
    # Select the required number of players for this category  
    for i in range(count):
        if i < len(category_players): 
            # Get the player with highest composite score that fits the budget 
            affordable_players = category_players[category_players['price'] <= remaining_budget]

            if affordable_players.empty:
                # No affordable players found, try to find cheaper alternative
                continue
                
            selected_player = affordable_players.iloc[0]
            
            # Add selected subtitutes 
            player_dict = {
                'player_id' : selected_player['player_id'],
                'name' : selected_player['name'],
                'position' : selected_player['position'],
                'team': selected_player['team'],
                'price': selected_player['price'],
                'performance_score': selected_player['performance_score'],
                'form': selected_player['form']
            }
            selected_subs.append(player_dict) 
            
            # Update remaining budget 
            remaining_budget -= selected_player['price']
            
            # Remove selected player from available players 
            available_players = available_players[available_players['player_id'] != selected_player['player_id']]
            category_players = category_players[category_players['player_id'] != selected_player['player_id']]
            
    return selected_subs
    
def optimize_team_for_opponent(
    current_squad: List[Dict[str, Any]],
    opponent_team: str,
    fixtures_df: pd.DataFrame,
    teams_df: pd.DataFrame
) -> List[Dict[str, Any]]: 
    """
    Optimize starting line-up based on upcoming opponent 
    
    Args:
        current_squad: List of player dictionaries in the current squad
        opponent_team : Name of the upcoming opponent 
        fixtures_df: DataFrame containing fixture information 
        teams_df: DataFrame containing team information     
    
    Returns:
        List of dictionaries containing optimized starting XI    
    """
    
    # Get opponent strength 
    opponent_strength = teams_df.loc[teams_df['name'] == opponent_team, 'strength'].values[0] if not teams_df.empty else 75 
    
    # Adjust player scores based on opponent strength 
    for player in current_squad:
        # Check if player has a match against the opponent 
        if player['teams'] == opponent_team:
            # Player is on the opponent team (shouldn't happen, but just in case)
            adjustment = 0
        else:
            # Find if player's team is playing home or away 
            is_home = False
            
            # Look for the fixture in fixtures_df 
            home_match = fixtures_df[(fixtures_df['home_team'] == player['team']) & 
                                     (fixtures_df['away_team'] == opponent_team)]
            away_match = fixtures_df[(fixtures_df['away_team'] == player['team']) & 
                                     (fixtures_df['home_team'] == opponent_team)]
            
            if not home_match.empty:
                is_home=True
                
            # Calculate adjustment factor based on opponent strength and home/away 
            base_adjustment = (75-opponent_strength)/75 # Positive if opponent is weak, negative is strong
            home_factor = 0.1 if is_home else -0.1
            
            adjustement = base_adjustment + home_factor
            
        # Apply adjustment to player's score
        player['adjusted_score'] = player['performance_score'] * (1+adjustment)
    
    # Sort players by adjusted score within each position
    position_groups = {} 
    for player in current_squad: 
        position = player['position']
        if position not in position_groups:
            position_groups[position] = []
        position_groups[position].append(player)
        
    # Sort each position group 
    for position in position_groups:
        position_groups[position].sort(key=lambda p:p.get('adjusted_score', p['performance_score']), reverse=True)
        
    # Select starting XI based on required positions and highest adjusted scores
    starting_xi = []
    for position, count in positions_required.items():
        # Skip substitute positions 
        if position in ['SUB GK', 'SUB DEF', 'SUB MID', 'SUB FWD']:
            continue 
        
        # Check if we have players for this position
        if position in position_groups:
            # Add the top players for this position 
            for i in range(min(count, len(position_groups[position]))):
                starting_xi.append(position_groups[position][i])
    
    return starting_xi