import pandas as pd
from typing import Dict, Any, Optional


def get_opponent_strength(
    team: str, 
    gameweek: int, 
    fixtures_df: pd.DataFrame, 
    teams_df: pd.DataFrame
) -> Optional[Dict[str, Any]]:
    """
    Get information about a team's next opponent
    
    Args:
        team: The team name
        gameweek: Current gameweek number
        fixtures_df: DataFrame containing fixture information
        teams_df: DataFrame containing team information
        
    Returns:
        Dictionary containing opponent information or None if no fixture found
    """
    # Find the fixture for the specified team and gameweek
    home_fixture = fixtures_df[(fixtures_df['home_team'] == team) & (fixtures_df['gameweek'] == gameweek)]
    away_fixture = fixtures_df[(fixtures_df['away_team'] == team) & (fixtures_df['gameweek'] == gameweek)]
    
    if not home_fixture.empty:
        # Team is playing at home
        opponent = home_fixture.iloc[0]['away_team']
        is_home = True
    elif not away_fixture.empty:
        # Team is playing away
        opponent = away_fixture.iloc[0]['home_team']
        is_home = False
    else:
        # No fixture found for this gameweek
        return None
    
    # Get opponent strength from teams_df
    if not teams_df.empty:
        opponent_strength = teams_df.loc[teams_df['name'] == opponent, 'strength'].values[0]
        opponent_position = teams_df.loc[teams_df['name'] == opponent, 'position'].values[0]
    else:
        # Default values if team not found
        opponent_strength = 75
        opponent_position = 10
    
    # Calculate expected difficulty (1-5 scale)
    # Factors: opponent strength, home/away advantage, opponent league position
    base_difficulty = opponent_strength / 20  # Convert 0-100 scale to 0-5 scale
    
    # Adjust for home/away
    if is_home:
        difficulty_adjustment = -0.5  # Home advantage reduces difficulty
    else:
        difficulty_adjustment = 0.5  # Away matches are harder
    
    # Adjust for opponent position (lower position = easier opponent)
    position_adjustment = (10 - opponent_position) / 10  # Range: -1 to +1
    
    # Calculate final difficulty (1-5 scale)
    expected_difficulty = max(1, min(5, base_difficulty + difficulty_adjustment + position_adjustment))
    
    return {
        'opponent': opponent,
        'is_home': is_home,
        'strength': opponent_strength,
        'position': opponent_position,
        'expected_difficulty': round(expected_difficulty, 1)
    }


def adjust_score_for_opponent(
    performance_score: float,
    opponent_strength: float,
    is_home: bool
) -> float:
    """
    Adjust player performance score based on opponent strength and home/away status
    
    Args:
        performance_score: Player's base performance score
        opponent_strength: Opponent team strength (0-100)
        is_home: Whether the player's team is playing at home
        
    Returns:
        Adjusted performance score
    """
    # Baseline strength (average team)
    baseline_strength = 75
    
    # Calculate strength difference
    strength_diff = baseline_strength - opponent_strength
    
    # Normalize to a factor between -0.2 and +0.2
    strength_factor = strength_diff / 250  # 50 point difference = ±0.2 adjustment
    
    # Home advantage factor
    home_factor = 0.1 if is_home else -0.05
    
    # Calculate final adjustment
    adjustment = 1.0 + strength_factor + home_factor
    
    # Apply adjustment to performance score
    adjusted_score = performance_score * adjustment
    
    return adjusted_score


def calculate_fixture_difficulty_rating(
    team: str,
    opponent: str,
    is_home: bool,
    teams_df: pd.DataFrame
) -> float:
    """
    Calculate fixture difficulty rating (FDR) for a team against an opponent
    
    Args:
        team: The team name
        opponent: The opponent team name
        is_home: Whether the team is playing at home
        teams_df: DataFrame containing team information
        
    Returns:
        Fixture difficulty rating (1-5 scale, with 5 being most difficult)
    """
    # Get team and opponent strengths
    if not teams_df.empty:
        team_strength = teams_df.loc[teams_df['name'] == team, 'strength'].values[0]
        opponent_strength = teams_df.loc[teams_df['name'] == opponent, 'strength'].values[0]
        opponent_position = teams_df.loc[teams_df['name'] == opponent, 'position'].values[0]
    else:
        # Default values if team not found
        team_strength = 75
        opponent_strength = 75
        opponent_position = 10
    
    # Calculate base difficulty based on strength difference
    strength_diff = opponent_strength - team_strength
    base_difficulty = 3 + (strength_diff / 25)  # 25 point difference = 1 point on FDR scale
    
    # Adjust for home/away
    if is_home:
        difficulty_adjustment = -0.5  # Home advantage reduces difficulty
    else:
        difficulty_adjustment = 0.5  # Away matches are harder
    
    # Adjust for opponent position (lower position = easier opponent)
    position_factor = (10 - opponent_position) / 20  # Range: -0.5 to +0.5
    
    # Calculate final FDR (1-5 scale)
    fdr = base_difficulty + difficulty_adjustment - position_factor
    
    # Ensure FDR is within 1-5 range
    fdr = max(1, min(5, fdr))
    
    return round(fdr, 1)


def get_fixture_difficulty_trend(
    team: str,
    current_gameweek: int,
    num_gameweeks: int,
    fixtures_df: pd.DataFrame,
    teams_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Calculate fixture difficulty trend for upcoming gameweeks
    
    Args:
        team: The team name
        current_gameweek: Current gameweek number
        num_gameweeks: Number of gameweeks to analyze
        fixtures_df: DataFrame containing fixture information
        teams_df: DataFrame containing team information
        
    Returns:
        Dictionary containing fixture difficulty information
    """
    # List to store fixture difficulties
    fixtures_info = []
    
    # Analyze upcoming fixtures
    for gw in range(current_gameweek, current_gameweek + num_gameweeks):
        if gw > 38:  # Season only has 38 gameweeks
            break
            
        # Get opponent for this gameweek
        opponent_info = get_opponent_strength(team, gw, fixtures_df, teams_df)
        
        if opponent_info:
            fixtures_info.append({
                'gameweek': gw,
                'opponent': opponent_info['opponent'],
                'is_home': opponent_info['is_home'],
                'difficulty': opponent_info['expected_difficulty']
            })
    
    # Calculate average difficulty
    if fixtures_info:
        avg_difficulty = sum(fixture['difficulty'] for fixture in fixtures_info) / len(fixtures_info)
    else:
        avg_difficulty = 3.0  # Default medium difficulty
    
    # Determine fixture trend
    if len(fixtures_info) >= 2:
        # Compare difficulty of first half vs second half of fixtures
        half_point = len(fixtures_info) // 2
        first_half = fixtures_info[:half_point]
        second_half = fixtures_info[half_point:]
        
        first_half_avg = sum(fixture['difficulty'] for fixture in first_half) / len(first_half)
        second_half_avg = sum(fixture['difficulty'] for fixture in second_half) / len(second_half)
        
        if first_half_avg > second_half_avg + 0.5:
            trend = "Improving"  # Fixtures get easier
        elif second_half_avg > first_half_avg + 0.5:
            trend = "Worsening"  # Fixtures get harder
        else:
            trend = "Stable"     # No significant change
    else:
        trend = "Unknown"  # Not enough fixtures to determine trend
    
    return {
        'team': team,
        'fixtures': fixtures_info,
        'avg_difficulty': round(avg_difficulty, 1),
        'trend': trend
    }
