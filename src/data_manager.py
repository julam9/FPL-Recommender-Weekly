import pandas as pd
import os
import json
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

# Import web scraper
try:
    from web_scraper import update_data_from_web, get_latest_data_from_web
    WEB_SCRAPER_AVAILABLE = True
except ImportError:
    WEB_SCRAPER_AVAILABLE = False 
    
def load_data(current_gameweek: int, use_web_data: bool = False, league: str = "premier_league") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load data files for players, teams, fixtures, and performance history.
    If files don't exist, create sample data or fetch from web if requested.
    
    Args:
        current_gameweek: The current gameweek number
        use_web_data: Whether to attempt to fetch data from web sources
        league: League name for web data scraping
        
    Returns:
        Tuple of DataFrames: (players_df, teams_df, fixtures_df, performance_history_df)
    """
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Try to fetch data from web if requested
    if use_web_data and WEB_SCRAPER_AVAILABLE:
        try:
            web_players_df, web_teams_df, web_fixtures_df, web_performance_history_df = update_data_from_web(
                current_gameweek=current_gameweek, 
                league=league
            )
            
            # If we successfully got data from the web, return it
            if (not web_players_df.empty and not web_teams_df.empty and 
                not web_fixtures_df.empty and not web_performance_history_df.empty):
                return web_players_df, web_teams_df, web_fixtures_df, web_performance_history_df
        except Exception as e:
            print(f"Error fetching web data: {str(e)}")
            print("Falling back to local data...")
    
    # Load players data
    players_file = 'data/players.csv'
    if os.path.exists(players_file):
        players_df = pd.read_csv(players_file)
    else:
        # Create sample players data
        players_df = create_sample_player_data()
        players_df.to_csv(players_file, index=False)
        
    # Load teams data
    teams_file = 'data/teams.csv'
    if os.path.exists(teams_file):
        teams_df = pd.read_csv(teams_file)
    else:
        # Create sample teams data
        teams_df = create_sample_team_data()
        teams_df.to_csv(teams_file, index=False)
        
    # Load fixtures data
    fixtures_file = 'data/fixtures.csv'
    if os.path.exists(fixtures_file):
        fixtures_df = pd.read_csv(fixtures_file)
    else:
        # Create sample fixtures data
        fixtures_df = create_sample_fixture_data(teams_df)
        fixtures_df.to_csv(fixtures_file, index=False)
        
    # Load performance history
    performance_file = 'data/performance_history.csv'
    if os.path.exists(performance_file):
        performance_history_df = pd.read_csv(performance_file)
    else:
        # Create sample performance history
        performance_history_df = create_sample_performance_history(players_df, current_gameweek)
        performance_history_df.to_csv(performance_file, index=False)
    
    return players_df, teams_df, fixtures_df, performance_history_df 

def save_data(squad: List[Dict[str, Any]], manager: Dict[str, Any], gameweek: int) -> None:
    """
    Save current squad and manager selection to file
    
    Args:
        squad: List of dictionaries containing player information
        manager: Dictionary containing manager information
        gameweek: Current gameweek number
    """
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Create data to save
    data = {
        'gameweek': gameweek,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'squad': squad,
        'manager': manager
    }
    
    # Save to file
    with open(f'data/squad_gw{gameweek}.json', 'w') as f:
        json.dump(data, f, indent=4)

def update_player_availability(player_id: int, is_available: bool, reason: str = None) -> None:
    """
    Update player availability status
    
    Args:
        player_id: The player's ID
        is_available: True if player is available, False otherwise
        reason: Reason for unavailability (injury, suspension, etc.)
    """
    players_file = 'data/players.csv'
    if os.path.exists(players_file):
        players_df = pd.read_csv(players_file)
        
        # Update player availability
        players_df.loc[players_df['player_id'] == player_id, 'is_available'] = is_available
        
        if not is_available and reason:
            players_df.loc[players_df['player_id'] == player_id, 'unavailability_reason'] = reason
        elif is_available:
            players_df.loc[players_df['player_id'] == player_id, 'unavailability_reason'] = None
        
        # Save updated data
        players_df.to_csv(players_file, index=False) 
        
def fetch_specific_data(data_type: str, team_name: str = None, player_name: str = None, 
                       league: str = "premier_league") -> Optional[pd.DataFrame]:
    """
    Fetch specific data from web sources
    
    Args:
        data_type: Type of data to fetch ('players', 'teams', 'fixtures', 'performance')
        team_name: Optional team name to filter results
        player_name: Optional player name to filter results
        league: League name to scrape data from
        
    Returns:
        DataFrame containing the fetched data or None if unsuccessful
    """
    if not WEB_SCRAPER_AVAILABLE:
        print("Web scraper is not available. Please make sure trafilatura is installed.")
        return None
        
    try:
        data = get_latest_data_from_web(
            data_type=data_type, 
            team_name=team_name, 
            player_name=player_name, 
            league=league
        )
        
        if not data.empty:
            # Save the data to file
            file_path = f'data/{data_type}.csv'
            if os.path.exists(file_path):
                # If file exists, we'll update it rather than overwrite
                existing_data = pd.read_csv(file_path)
                
                # Merging strategy depends on the data type
                if data_type == 'players':
                    # For players, update existing entries and add new ones
                    combined_data = pd.concat([existing_data, data]).drop_duplicates(subset=['player_id'], keep='last')
                elif data_type == 'teams':
                    # For teams, update existing entries and add new ones
                    combined_data = pd.concat([existing_data, data]).drop_duplicates(subset=['team_id'], keep='last')
                elif data_type == 'fixtures':
                    # For fixtures, update existing entries and add new ones
                    combined_data = pd.concat([existing_data, data]).drop_duplicates(subset=['fixture_id'], keep='last')
                elif data_type == 'performance':
                    # For performance, we might want to append new entries
                    combined_data = pd.concat([existing_data, data])
                    # Remove duplicates if any
                    if 'player_name' in combined_data.columns and 'gameweek' in combined_data.columns:
                        combined_data = combined_data.drop_duplicates(subset=['player_name', 'gameweek'], keep='last')
                
                # Save the combined data
                combined_data.to_csv(file_path, index=False)
                return combined_data
            else:
                # If file doesn't exist, just save the new data
                data.to_csv(file_path, index=False)
                return data
        else:
            print(f"No {data_type} data found for the specified parameters.")
            return None
    except Exception as e:
        print(f"Error fetching {data_type} data: {str(e)}")
        return None
    
def create_sample_player_data() -> pd.DataFrame:
    """
    Create sample player data for initial setup
    
    Returns:
        DataFrame containing sample player data
    """
    # List of teams
    teams = [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Leeds", 
        "Leicester", "Liverpool", "Man City", "Man United", "Newcastle", 
        "Nottingham Forest", "Southampton", "Tottenham", "West Ham", "Wolves"
    ]
    
    # Sample player data
    players_data = []
    player_id = 1
    
    # Sample names by position
    gk_names = ["Alisson", "Ederson", "De Gea", "Lloris", "Ramsdale", "Mendy", "Pickford", "Pope", "Kepa", "Leno"]
    rb_names = ["Alexander-Arnold", "Walker", "James", "Wan-Bissaka", "Cash", "Trippier", "Cancelo", "Tomiyasu", "Lamptey", "Dalot"]
    cb_names = ["Van Dijk", "Dias", "Silva", "Maguire", "Stones", "Varane", "Laporte", "Gabriel", "Romero", "Dunk",
               "Konsa", "Mings", "Guehi", "Anderson", "Kilman", "Fofana", "Saliba", "Martinez", "Botman", "Koulibaly"]
    lb_names = ["Robertson", "Shaw", "Chilwell", "Zinchenko", "Targett", "Tierney", "Reguillon", "Digne", "Cresswell", "Malacia"]
    dm_names = ["Rodri", "Kante", "Fabinho", "Rice", "Casemiro", "Partey", "Phillips", "Bissouma", "Douglas Luiz", "Neves"]
    cm_names = ["De Bruyne", "Fernandes", "Bernardo", "Mount", "Thiago", "Odegaard", "Grealish", "Maddison", "Tielemans", "Ward-Prowse"]
    am_names = ["Foden", "Saka", "Bellingham", "Elliott", "Smith Rowe", "Gallagher", "Ramsey", "Palmer", "Eriksen", "Gordon"]
    rw_names = ["Salah", "Mahrez", "Sancho", "Bowen", "Raphinha", "Antony", "Kulusevski", "Sterling", "Martinelli", "Sarr"]
    st_names = ["Haaland", "Kane", "Ronaldo", "Jesus", "Vardy", "Toney", "Nunez", "Mitrovic", "Wilson", "Isak"]
    lw_names = ["Son", "Mane", "Rashford", "Saint-Maximin", "Podence", "Zaha", "Bailey", "Coutinho", "Perisic", "Diaz"]
    
    # Create goalkeepers
    for i, name in enumerate(gk_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'GK',
            'team': team,
            'price': round(3.5 + (i * 0.5), 1),  # Price between 3.5 and 8.0
            'performance_score': round(50 + (i * 5), 1),  # Performance between 50 and 95
            'form': round(5 + (i * 0.5), 1),  # Form between 5 and 10
            'goals': 0,
            'assists': 0,
            'clean_sheets': i,
            'minutes_played': 90 * (7 + (i % 3)),
            'is_available': True if i < 8 else False,
            'unavailability_reason': None if i < 8 else 'Injury'
        })
        player_id += 1
    
    # Create right backs
    for i, name in enumerate(rb_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'RB',
            'team': team,
            'price': round(4.0 + (i * 0.5), 1),  # Price between 4.0 and 8.5
            'performance_score': round(50 + (i * 5), 1),  # Performance between 50 and 95
            'form': round(5 + (i * 0.5), 1),  # Form between 5 and 10
            'goals': i % 3,
            'assists': i,
            'clean_sheets': i % 5,
            'minutes_played': 90 * (7 + (i % 4)),
            'is_available': True if i < 9 else False,
            'unavailability_reason': None if i < 9 else 'Suspension'
        })
        player_id += 1
    
    # Create center backs
    for i, name in enumerate(cb_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'CB',
            'team': team,
            'price': round(4.0 + (i * 0.3), 1),  # Price between 4.0 and 9.7
            'performance_score': round(50 + (i * 2.5), 1),  # Performance between 50 and 97.5
            'form': round(5 + (i * 0.25), 1),  # Form between 5 and 10
            'goals': i % 4,
            'assists': i % 3,
            'clean_sheets': i % 6,
            'minutes_played': 90 * (7 + (i % 4)),
            'is_available': True if i < 18 else False,
            'unavailability_reason': None if i < 18 else ('Injury' if i % 2 == 0 else 'Personal Reasons')
        })
        player_id += 1
    
    # Create left backs
    for i, name in enumerate(lb_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'LB',
            'team': team,
            'price': round(4.0 + (i * 0.5), 1),  # Price between 4.0 and 8.5
            'performance_score': round(50 + (i * 5), 1),  # Performance between 50 and 95
            'form': round(5 + (i * 0.5), 1),  # Form between 5 and 10
            'goals': i % 3,
            'assists': i,
            'clean_sheets': i % 5,
            'minutes_played': 90 * (7 + (i % 4)),
            'is_available': True if i < 9 else False,
            'unavailability_reason': None if i < 9 else 'Injury'
        })
        player_id += 1
    
    # Create defensive midfielders
    for i, name in enumerate(dm_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'DM',
            'team': team,
            'price': round(4.5 + (i * 0.5), 1),  # Price between 4.5 and 9.0
            'performance_score': round(50 + (i * 5), 1),  # Performance between 50 and 95
            'form': round(5 + (i * 0.5), 1),  # Form between 5 and 10
            'goals': i % 3,
            'assists': i % 4,
            'clean_sheets': 0,
            'key_passes': i * 2,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 8 else False,
            'unavailability_reason': None if i < 8 else ('Injury' if i % 2 == 0 else 'Suspension')
        })
        player_id += 1
    
    # Create central midfielders
    for i, name in enumerate(cm_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'CM',
            'team': team,
            'price': round(5.0 + (i * 0.8), 1),  # Price between 5.0 and 12.2
            'performance_score': round(60 + (i * 4), 1),  # Performance between 60 and 96
            'form': round(6 + (i * 0.4), 1),  # Form between 6 and 9.6
            'goals': i % 5,
            'assists': i % 7,
            'clean_sheets': 0,
            'key_passes': i * 3,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 9 else False,
            'unavailability_reason': None if i < 9 else 'Injury'
        })
        player_id += 1
    
    # Create attacking midfielders
    for i, name in enumerate(am_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'AM',
            'team': team,
            'price': round(5.5 + (i * 0.7), 1),  # Price between 5.5 and 11.8
            'performance_score': round(60 + (i * 4), 1),  # Performance between 60 and 96
            'form': round(6 + (i * 0.4), 1),  # Form between 6 and 9.6
            'goals': i % 6,
            'assists': i % 8,
            'clean_sheets': 0,
            'key_passes': i * 4,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 8 else False,
            'unavailability_reason': None if i < 8 else 'Not Selected'
        })
        player_id += 1
    
    # Create right wingers
    for i, name in enumerate(rw_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'RW',
            'team': team,
            'price': round(6.0 + (i * 1.0), 1),  # Price between 6.0 and 15.0
            'performance_score': round(70 + (i * 3), 1),  # Performance between 70 and 97
            'form': round(7 + (i * 0.3), 1),  # Form between 7 and 9.7
            'goals': i % 10,
            'assists': i % 8,
            'clean_sheets': 0,
            'key_passes': i * 3,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 9 else False,
            'unavailability_reason': None if i < 9 else 'Injury'
        })
        player_id += 1
    
    # Create strikers
    for i, name in enumerate(st_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'ST',
            'team': team,
            'price': round(6.5 + (i * 1.2), 1),  # Price between 6.5 and 17.3
            'performance_score': round(70 + (i * 3), 1),  # Performance between 70 and 97
            'form': round(7 + (i * 0.3), 1),  # Form between 7 and 9.7
            'goals': i + 2,
            'assists': i % 5,
            'clean_sheets': 0,
            'key_passes': i * 2,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 8 else False,
            'unavailability_reason': None if i < 8 else ('Injury' if i % 2 == 0 else 'Suspension')
        })
        player_id += 1
    
    # Create left wingers
    for i, name in enumerate(lw_names):
        team = teams[i % len(teams)]
        players_data.append({
            'player_id': player_id,
            'name': name,
            'position': 'LW',
            'team': team,
            'price': round(6.0 + (i * 1.0), 1),  # Price between 6.0 and 15.0
            'performance_score': round(70 + (i * 3), 1),  # Performance between 70 and 97
            'form': round(7 + (i * 0.3), 1),  # Form between 7 and 9.7
            'goals': i % 8,
            'assists': i % 9,
            'clean_sheets': 0,
            'key_passes': i * 3,
            'minutes_played': 90 * (6 + (i % 5)),
            'is_available': True if i < 8 else False,
            'unavailability_reason': None if i < 8 else 'Injury'
        })
        player_id += 1
    
    # Create DataFrame
    players_df = pd.DataFrame(players_data)
    return players_df 

def create_sample_team_data() -> pd.DataFrame:
    """
    Create sample team data for initial setup
    
    Returns:
        DataFrame containing sample team data
    """
    # List of teams and their managers
    teams_data = [
        {"name": "Arsenal", "manager_name": "Mikel Arteta", "manager_rating": 8.2, "position": 2, "strength": 85},
        {"name": "Aston Villa", "manager_name": "Unai Emery", "manager_rating": 7.8, "position": 7, "strength": 77},
        {"name": "Bournemouth", "manager_name": "Andoni Iraola", "manager_rating": 6.5, "position": 15, "strength": 65},
        {"name": "Brentford", "manager_name": "Thomas Frank", "manager_rating": 7.6, "position": 9, "strength": 75},
        {"name": "Brighton", "manager_name": "Roberto De Zerbi", "manager_rating": 8.0, "position": 6, "strength": 78},
        {"name": "Chelsea", "manager_name": "Mauricio Pochettino", "manager_rating": 7.7, "position": 8, "strength": 80},
        {"name": "Crystal Palace", "manager_name": "Oliver Glasner", "manager_rating": 7.2, "position": 12, "strength": 73},
        {"name": "Everton", "manager_name": "Sean Dyche", "manager_rating": 6.8, "position": 16, "strength": 68},
        {"name": "Fulham", "manager_name": "Marco Silva", "manager_rating": 7.0, "position": 13, "strength": 71},
        {"name": "Leeds", "manager_name": "Daniel Farke", "manager_rating": 6.7, "position": 17, "strength": 67},
        {"name": "Leicester", "manager_name": "Steve Cooper", "manager_rating": 6.9, "position": 14, "strength": 70},
        {"name": "Liverpool", "manager_name": "Jurgen Klopp", "manager_rating": 8.7, "position": 3, "strength": 87},
        {"name": "Man City", "manager_name": "Pep Guardiola", "manager_rating": 9.2, "position": 1, "strength": 90},
        {"name": "Man United", "manager_name": "Erik ten Hag", "manager_rating": 7.5, "position": 10, "strength": 82},
        {"name": "Newcastle", "manager_name": "Eddie Howe", "manager_rating": 8.1, "position": 5, "strength": 83},
        {"name": "Nottingham Forest", "manager_name": "Nuno Espirito Santo", "manager_rating": 6.6, "position": 18, "strength": 66},
        {"name": "Southampton", "manager_name": "Russell Martin", "manager_rating": 6.4, "position": 19, "strength": 63},
        {"name": "Tottenham", "manager_name": "Ange Postecoglou", "manager_rating": 7.9, "position": 4, "strength": 84},
        {"name": "West Ham", "manager_name": "David Moyes", "manager_rating": 7.3, "position": 11, "strength": 74},
        {"name": "Wolves", "manager_name": "Gary O'Neil", "manager_rating": 6.5, "position": 20, "strength": 64}
    ]
    
    # Create DataFrame
    teams_df = pd.DataFrame(teams_data)
    return teams_df

def create_sample_fixture_data(teams_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create sample fixture data for the season
    
    Args:
        teams_df: DataFrame containing team information
        
    Returns:
        DataFrame containing sample fixture data
    """
    if teams_df.empty:
        teams_df = create_sample_team_data()
    
    teams = teams_df['name'].tolist()
    total_teams = len(teams)
    
    fixtures_data = []
    fixture_id = 1
    
    # Generate fixtures for 38 gameweeks
    for gameweek in range(1, 39):
        # Each team plays once per gameweek
        teams_copy = teams.copy()
        
        # Shuffle teams to create random fixtures
        import random
        random.shuffle(teams_copy)
        
        # Create fixtures for this gameweek
        for i in range(0, total_teams, 2):
            if i + 1 < total_teams:
                home_team = teams_copy[i]
                away_team = teams_copy[i + 1]
                
                home_strength = teams_df.loc[teams_df['name'] == home_team, 'strength'].values[0]
                away_strength = teams_df.loc[teams_df['name'] == away_team, 'strength'].values[0]
                
                # Calculate expected goals based on team strengths and home advantage
                home_xg = round((home_strength / 10) + 0.3, 1)  # Home advantage
                away_xg = round(away_strength / 10, 1)
                
                fixtures_data.append({
                    'fixture_id': fixture_id,
                    'gameweek': gameweek,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_xg': home_xg,
                    'away_xg': away_xg,
                    'played': gameweek < 10,  # First 9 gameweeks have been played
                    'home_score': int(round(home_xg)) if gameweek < 10 else None,
                    'away_score': int(round(away_xg)) if gameweek < 10 else None
                })
                
                fixture_id += 1
    
    # Create DataFrame
    fixtures_df = pd.DataFrame(fixtures_data)
    return fixtures_df

def create_sample_performance_history(players_df: pd.DataFrame, current_gameweek: int) -> pd.DataFrame:
    """
    Create sample performance history for players
    
    Args:
        players_df: DataFrame containing player information
        current_gameweek: The current gameweek number
        
    Returns:
        DataFrame containing sample performance history
    """
    if players_df.empty:
        players_df = create_sample_player_data()
    
    performance_data = []
    
    # Generate performance data for each player for past gameweeks
    for _, player in players_df.iterrows():
        base_performance = player['performance_score']
        
        for gameweek in range(1, min(current_gameweek + 1, 10)):  # Up to current gameweek or max 9
            # Randomize performance score around base score
            import random
            
            # Performance varies by ±20%
            performance_variation = random.uniform(-0.2, 0.2)
            performance_score = base_performance * (1 + performance_variation)
            
            # Vary stats based on position
            position = player['position']
            goals = 0
            assists = 0
            clean_sheets = 0
            key_passes = 0
            
            if gameweek % 2 == 0:  # Add some scoring pattern
                if position in ['ST', 'LW', 'RW']:
                    goals = random.randint(0, 2)
                    assists = random.randint(0, 1)
                    key_passes = random.randint(1, 4)
                elif position in ['AM', 'CM']:
                    goals = random.randint(0, 1)
                    assists = random.randint(0, 2)
                    key_passes = random.randint(2, 6)
                elif position in ['DM', 'RB', 'LB']:
                    goals = 1 if random.random() < 0.1 else 0
                    assists = random.randint(0, 1)
                    clean_sheets = 1 if random.random() < 0.3 else 0
                    key_passes = random.randint(1, 3)
                elif position in ['CB', 'GK']:
                    clean_sheets = 1 if random.random() < 0.4 else 0
            
            # Minutes played (with some variation)
            minutes = random.randint(0, 90)
            if minutes > 60:  # Most likely play full game if over 60 mins
                minutes = 90
            
            # Form is moving average of recent performances
            form = min(10, max(1, performance_score / 10))
            
            performance_data.append({
                'player_id': player['player_id'],
                'name': player['name'],
                'position': position,
                'team': player['team'],
                'gameweek': gameweek,
                'performance_score': round(performance_score, 1),
                'goals': goals,
                'assists': assists,
                'clean_sheets': clean_sheets,
                'key_passes': key_passes,
                'minutes_played': minutes,
                'form': round(form, 1)
            })
    
    # Create DataFrame
    performance_history_df = pd.DataFrame(performance_data)
    return performance_history_df
