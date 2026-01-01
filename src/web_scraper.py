import trafilatura
import pandas as pd
import re
import json
import time
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract the main text content of a website.
    
    Args:
        url: URL of the website to scrape
        
    Returns:
        Extracted text content
    """
    try:
        logger.info(f"Fetching content from {url}")
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            logger.error(f"Failed to download content from {url}")
            return ""
            
        text = trafilatura.extract(downloaded)
        
        if text is None:
            logger.error(f"Failed to extract text content from {url}")
            return ""
            
        return text
    except Exception as e:
        logger.error(f"Error while scraping {url}: {str(e)}")
        return ""
    
def scrape_team_data(league: str = "premier_league", season: str = "2024-2025") -> pd.DataFrame:
    """
    Scrape team data from football statistics websites.
    
    Args:
        league: League name (e.g., premier_league, la_liga)
        season: Season identifier (e.g., 2024-2025)
        
    Returns:
        DataFrame containing team information
    """
    # Example URL patterns for different leagues
    url_patterns = {
        "premier_league": f"https://www.premierleague.com/en/clubs",
    }
    
    if league not in url_patterns:
        logger.error(f"Unsupported league: {league}")
        return pd.DataFrame()
    
    url = url_patterns[league]
    content = get_website_text_content(url)
    
    # Process the extracted content to create a DataFrame
    # This is a simplified example - real implementation would need
    # to parse the specific structure of each website
    teams = []
    team_names = re.findall(r'([A-Za-z ]+) Official Website', content)
    
    for idx, name in enumerate(team_names):
        teams.append({
            'team_id': idx + 1,
            'name': name.strip(),
            'league': league,
            'season': season,
            'strength': 75,  # Default value, will be updated with real data
            'home_advantage': 10  # Default value, will be updated with real data
        })
    
    return pd.DataFrame(teams)

def scrape_paginated_content(base_url: str, max_pages: int = 50, page_param: str = "page") -> List[str]:
    """
    Scrape content from multiple pages by iterating through pagination.
    
    Args:
        base_url: Base URL for the paginated content
        max_pages: Maximum number of pages to scrape
        page_param: URL parameter name for page number
        
    Returns:
        List of text content from all pages
    """
    all_content = []
    empty_pages_count = 0
    max_empty_pages = 3  # Stop if we encounter 3 consecutive empty pages
    
    for page_num in range(1, max_pages + 1):
        try:
            # Construct URL for current page
            if "?" in base_url:
                page_url = f"{base_url}&{page_param}={page_num}"
            else:
                page_url = f"{base_url}?{page_param}={page_num}"
            
            logger.info(f"Scraping page {page_num}: {page_url}")
            
            # Get content from current page
            content = get_website_text_content(page_url)
            
            # Check if page has meaningful content
            if len(content.strip()) < 100:  # Assume empty if less than 100 characters
                empty_pages_count += 1
                logger.warning(f"Page {page_num} appears to be empty or have minimal content")
                
                if empty_pages_count >= max_empty_pages:
                    logger.info(f"Stopping pagination after {max_empty_pages} consecutive empty pages")
                    break
            else:
                empty_pages_count = 0  # Reset counter
                all_content.append(content)
                logger.info(f"Successfully scraped page {page_num}, content length: {len(content)}")
            
            # Add delay to be respectful to the server
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {str(e)}")
            empty_pages_count += 1
            
            if empty_pages_count >= max_empty_pages:
                break
    
    logger.info(f"Completed pagination scraping. Retrieved {len(all_content)} pages of content")
    return all_content

def scrape_paginated_players(league_url: str, max_pages: int = 20) -> pd.DataFrame:
    """
    Scrape player data from paginated football statistics websites.
    
    Args:
        league_url: Base URL for the league's player statistics
        max_pages: Maximum number of pages to scrape
        
    Returns:
        DataFrame containing comprehensive player information
    """
    logger.info(f"Starting paginated player scraping for: {league_url}")
    
    # Get content from all pages
    all_content = scrape_paginated_content(league_url, max_pages)
    
    if not all_content:
        logger.error("No content retrieved from any pages")
        return pd.DataFrame()
    
    # Combine all content
    combined_content = "\n".join(all_content)
    
    # Extract player information using comprehensive regex patterns
    players = []
    
    # Pattern 1: Name, Position, Team, Age, Market Value
    pattern1 = re.findall(r'([A-Za-z\s\-\'\.]+)\s+([A-Z]{2,3})\s+([A-Za-z\s]+)\s+(\d{1,2})\s+[\$€£]?([\d\.]+)[Mm]?', combined_content)
    
    for idx, match in enumerate(pattern1):
        if len(match) >= 5:
            name, position, team, age, value = match
            players.append({
                'player_id': idx + 1,
                'name': name.strip(),
                'position': position.strip(),
                'team': team.strip(),
                'age': int(age) if age.isdigit() else 25,
                'price': float(value) if value.replace('.', '').isdigit() else 5.0,
                'performance_score': 60,  # Default, will be updated with real metrics
                'form': 6.0,
                'goals': 0,
                'assists': 0,
                'clean_sheets': 0,
                'minutes_played': 0
            })
    
    # Pattern 2: More detailed stats if available
    detailed_pattern = re.findall(r'([A-Za-z\s\-\'\.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', combined_content)
    
    # Try to match detailed stats with existing players
    for match in detailed_pattern:
        if len(match) >= 5:
            name_part, goals, assists, appearances, minutes = match
            
            # Find matching player
            for player in players:
                if name_part.lower() in player['name'].lower():
                    player['goals'] = int(goals)
                    player['assists'] = int(assists)
                    player['minutes_played'] = int(minutes)
                    
                    # Calculate performance score based on stats
                    player['performance_score'] = calculate_performance_from_stats(
                        int(goals), int(assists), int(appearances), player['position']
                    )
                    break
    
    # Remove duplicates based on name similarity
    unique_players = []
    seen_names = set()
    
    for player in players:
        normalized_name = re.sub(r'[^a-zA-Z]', '', player['name'].lower())
        if normalized_name not in seen_names and len(normalized_name) > 2:
            seen_names.add(normalized_name)
            unique_players.append(player)
    
    logger.info(f"Extracted {len(unique_players)} unique players from {len(all_content)} pages")
    return pd.DataFrame(unique_players)

def calculate_performance_from_stats(goals: int, assists: int, appearances: int, position: str) -> float:
    """
    Calculate performance score based on player statistics.
    
    Args:
        goals: Number of goals scored
        assists: Number of assists
        appearances: Number of appearances
        position: Player position
        
    Returns:
        Performance score (0-100)
    """
    if appearances == 0:
        return 50  # Default score
    
    # Position-specific scoring
    if position in ['GK']:
        # Goalkeepers: Focus on clean sheets and saves
        base_score = 50 + min(goals * 10, 20)  # Goals are rare but valuable for GK
    elif position in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
        # Defenders: Goals and assists are valuable, clean sheets matter
        base_score = 50 + (goals * 6) + (assists * 4)
    elif position in ['CM', 'CDM', 'CAM', 'LM', 'RM']:
        # Midfielders: Balance of goals and assists
        base_score = 50 + (goals * 5) + (assists * 5)
    else:
        # Forwards: Goals are most important
        base_score = 50 + (goals * 7) + (assists * 3)
    
    # Adjust for appearances (consistency bonus)
    consistency_bonus = min(appearances / 30 * 10, 10)
    
    # Cap at 100
    return min(base_score + consistency_bonus, 100) 

def scrape_multiple_leagues(leagues: Dict[str, str], max_pages_per_league: int = 20) -> pd.DataFrame:
    """
    Scrape player data from multiple football leagues.
    
    Args:
        leagues: Dictionary mapping league names to their base URLs
        max_pages_per_league: Maximum pages to scrape per league
        
    Returns:
        Combined DataFrame with players from all leagues
    """
    all_players = []
    
    for league_name, league_url in leagues.items():
        logger.info(f"Scraping {league_name} from {league_url}")
        
        try:
            league_players = scrape_paginated_players(league_url, max_pages_per_league)
            
            if not league_players.empty:
                # Add league information
                league_players['league'] = league_name
                all_players.append(league_players)
                logger.info(f"Successfully scraped {len(league_players)} players from {league_name}")
            else:
                logger.warning(f"No players found for {league_name}")
                
        except Exception as e:
            logger.error(f"Error scraping {league_name}: {str(e)}")
    
    if all_players:
        combined_df = pd.concat(all_players, ignore_index=True)
        logger.info(f"Combined total: {len(combined_df)} players from {len(all_players)} leagues")
        return combined_df
    else:
        logger.error("No player data retrieved from any league")
        return pd.DataFrame()
    
def smart_url_builder(base_url: str, **params) -> List[str]:
    """
    Build multiple URLs for different pagination patterns commonly used by football websites.
    
    Args:
        base_url: Base URL
        **params: Additional parameters like page numbers, filters, etc.
        
    Returns:
        List of URLs to try
    """
    urls = []
    page_num = params.get('page', 1)
    
    # Common pagination patterns
    patterns = [
        f"{base_url}?page={page_num}",
        f"{base_url}?p={page_num}",
        f"{base_url}?offset={(page_num-1)*20}",
        f"{base_url}?start={(page_num-1)*20}",
        f"{base_url}/page/{page_num}",
        f"{base_url}/{page_num}",
        f"{base_url}?pagenum={page_num}",
        f"{base_url}?pageNumber={page_num}"
    ]
    
    # Add season/league parameters if provided
    if 'season' in params:
        patterns = [url + f"&season={params['season']}" for url in patterns]
    if 'league' in params:
        patterns = [url + f"&league={params['league']}" for url in patterns]
    
    return patterns

def scrape_team_data(league: str = "premier_league", season: str = "2023-2024") -> pd.DataFrame:
    """
    Scrape team data from football statistics websites.
    
    Args:
        league: League name (e.g., premier_league, la_liga)
        season: Season identifier (e.g., 2023-2024)
        
    Returns:
        DataFrame containing team information
    """
    # Example URL patterns for different leagues
    url_patterns = {
        "premier_league": f"https://www.premierleague.com/clubs",
        "la_liga": f"https://www.laliga.com/en-GB/clubs",
        # Add more leagues as needed
    }
    
    if league not in url_patterns:
        logger.error(f"Unsupported league: {league}")
        return pd.DataFrame()
    
    url = url_patterns[league]
    content = get_website_text_content(url)
    
    # Process the extracted content to create a DataFrame
    # This is a simplified example - real implementation would need
    # to parse the specific structure of each website
    teams = []
    team_names = re.findall(r'([A-Za-z ]+) Official Website', content)
    
    for idx, name in enumerate(team_names):
        teams.append({
            'team_id': idx + 1,
            'name': name.strip(),
            'league': league,
            'season': season,
            'strength': 75,  # Default value, will be updated with real data
            'home_advantage': 10  # Default value, will be updated with real data
        })
    
    return pd.DataFrame(teams)

def scrape_player_data(team_name: str = None, league: str = "premier_league", max_pages: int = 25) -> pd.DataFrame:
    """
    Scrape player data from football statistics websites with pagination support.
    
    Args:
        team_name: Optional team name to filter players
        league: League name (e.g., premier_league, la_liga)
        max_pages: Maximum number of pages to scrape
        
    Returns:
        DataFrame containing comprehensive player information
    """
    # Enhanced URL patterns for different leagues with pagination
    url_patterns = {
        "premier_league": "https://www.premierleague.com/players",
        "la_liga": "https://www.laliga.com/en-GB/players",
        "serie_a": "https://www.legaseriea.it/en/players",
        "bundesliga": "https://www.bundesliga.com/en/bundesliga/players",
        "ligue_1": "https://www.ligue1.com/players",
        "champions_league": "https://www.uefa.com/uefachampionsleague/players",
        # Add more leagues as needed
    }
    
    if league not in url_patterns:
        logger.error(f"Unsupported league: {league}")
        return pd.DataFrame()
    
    url = url_patterns[league]
    
    # Use enhanced pagination scraping
    players_df = scrape_paginated_players(url, max_pages)
    
    # Filter by team if specified
    if team_name and not players_df.empty:
        players_df = players_df[players_df['team'].str.lower().str.contains(team_name.lower(), na=False)]
        logger.info(f"Filtered to {len(players_df)} players from team: {team_name}")
    
    return players_df 

def scrape_fixture_data(league: str = "premier_league", season: str = "2023-2024") -> pd.DataFrame:
    """
    Scrape fixture data from football statistics websites.
    
    Args:
        league: League name (e.g., premier_league, la_liga)
        season: Season identifier (e.g., 2023-2024)
        
    Returns:
        DataFrame containing fixture information
    """
    # Example URL patterns for different leagues
    url_patterns = {
        "premier_league": f"https://www.premierleague.com/fixtures",
        "la_liga": f"https://www.laliga.com/en-GB/laliga-santander/calendar",
        # Add more leagues as needed
    }
    
    if league not in url_patterns:
        logger.error(f"Unsupported league: {league}")
        return pd.DataFrame()
    
    url = url_patterns[league]
    content = get_website_text_content(url)
    
    # Process the extracted content to create a DataFrame
    # This is a simplified example - real implementation would need
    # to parse the specific structure of each website
    fixtures = []
    
    # Extract fixture information using regex patterns
    # These patterns would need to be tailored to the specific website structure
    fixture_entries = re.findall(r'([A-Za-z ]+)\s+v\s+([A-Za-z ]+)\s+(\d+:\d+)', content)
    
    for idx, entry in enumerate(fixture_entries):
        if len(entry) >= 3:
            home_team, away_team, time = entry
            
            # Calculate gameweek (simplified example)
            gameweek = (idx // 10) + 1
            
            fixtures.append({
                'fixture_id': idx + 1,
                'home_team': home_team.strip(),
                'away_team': away_team.strip(),
                'gameweek': gameweek,
                'season': season,
                'league': league
            })
    
    return pd.DataFrame(fixtures)

def scrape_performance_data(team_name: str = None, player_name: str = None, 
                           league: str = "premier_league") -> pd.DataFrame:
    """
    Scrape player performance data from football statistics websites.
    
    Args:
        team_name: Optional team name to filter performances
        player_name: Optional player name to filter performances
        league: League name (e.g., premier_league, la_liga)
        
    Returns:
        DataFrame containing performance information
    """
    # Example URL patterns for different leagues
    url_patterns = {
        "premier_league": "https://www.premierleague.com/stats/top/players",
        "la_liga": "https://www.laliga.com/en-GB/stats",
        # Add more leagues as needed
    }
    
    if league not in url_patterns:
        logger.error(f"Unsupported league: {league}")
        return pd.DataFrame()
    
    url = url_patterns[league]
    content = get_website_text_content(url)
    
    # Process the extracted content to create a DataFrame
    # This is a simplified example - real implementation would need
    # to parse the specific structure of each website
    performances = []
    
    # Extract performance data using regex patterns
    # These patterns would need to be tailored to the specific website structure
    performance_entries = re.findall(r'([A-Za-z ]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', content)
    
    for idx, entry in enumerate(performance_entries):
        if len(entry) >= 5:
            name, goals, assists, passes, minutes = entry
            
            # Skip if we're filtering by player or team
            if player_name and name.strip().lower() != player_name.lower():
                continue
                
            # For team filtering, we would need additional information
            # Here we're assuming the team info is not directly available in this pattern
            
            # Calculate gameweek (simplified example)
            gameweek = (idx % 38) + 1
            
            performances.append({
                'player_name': name.strip(),
                'gameweek': gameweek,
                'goals': int(goals),
                'assists': int(assists),
                'key_passes': int(passes),
                'minutes_played': int(minutes),
                'clean_sheets': 0,  # Would need to be extracted from goalkeeper/defender stats
                'goals_conceded': 0  # Would need to be extracted from goalkeeper/defender stats
            })
    
    return pd.DataFrame(performances)

def update_data_from_web(current_gameweek: int, league: str = "premier_league", max_pages: int = 25) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Update all data by scraping from web sources with pagination support.
    
    Args:
        current_gameweek: Current gameweek number
        league: League name
        max_pages: Maximum number of pages to scrape per data type
        
    Returns:
        Tuple of updated DataFrames: (players_df, teams_df, fixtures_df, performance_history_df)
    """
    try:
        logger.info(f"Starting comprehensive data update for {league} (up to {max_pages} pages per type)")
        
        logger.info(f"Scraping team data for {league}")
        teams_df = scrape_team_data(league=league)
        
        logger.info(f"Scraping player data for {league} with pagination")
        players_df = scrape_player_data(league=league, max_pages=max_pages)
        
        logger.info(f"Scraping fixture data for {league}")
        fixtures_df = scrape_fixture_data(league=league)
        
        logger.info(f"Scraping performance data for {league}")
        performance_history_df = scrape_performance_data(league=league)
        
        # Save the updated data with timestamp
        import os
        os.makedirs('data', exist_ok=True)
        
        if not teams_df.empty:
            teams_df.to_csv('data/teams.csv', index=False)
            logger.info(f"Saved {len(teams_df)} teams to data/teams.csv")
            
        if not players_df.empty:
            players_df.to_csv('data/players.csv', index=False)
            logger.info(f"Saved {len(players_df)} players to data/players.csv")
            
        if not fixtures_df.empty:
            fixtures_df.to_csv('data/fixtures.csv', index=False)
            logger.info(f"Saved {len(fixtures_df)} fixtures to data/fixtures.csv")
            
        if not performance_history_df.empty:
            performance_history_df.to_csv('data/performance_history.csv', index=False)
            logger.info(f"Saved {len(performance_history_df)} performance records to data/performance_history.csv")
        
        logger.info("Data update completed successfully")
        return players_df, teams_df, fixtures_df, performance_history_df
    
    except Exception as e:
        logger.error(f"Error updating data from web: {str(e)}")
        # Return empty DataFrames on error
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
def scrape_with_multiple_strategies(base_url: str, max_pages: int = 25) -> List[str]:
    """
    Attempt multiple scraping strategies for robust pagination handling.
    
    Args:
        base_url: Base URL to scrape
        max_pages: Maximum pages to attempt
        
    Returns:
        List of successfully scraped content
    """
    all_content = []
    
    # Strategy 1: Standard page parameter
    logger.info("Trying pagination strategy 1: ?page=N")
    content = scrape_paginated_content(base_url, max_pages, "page")
    if content:
        all_content.extend(content)
        return all_content
    
    # Strategy 2: Offset-based pagination
    logger.info("Trying pagination strategy 2: ?offset=N")
    for page in range(1, min(max_pages + 1, 6)):  # Try fewer pages for offset
        try:
            offset = (page - 1) * 20
            if "?" in base_url:
                url = f"{base_url}&offset={offset}"
            else:
                url = f"{base_url}?offset={offset}"
            
            content = get_website_text_content(url)
            if content and len(content.strip()) > 100:
                all_content.append(content)
                time.sleep(1)
            else:
                break
        except Exception as e:
            logger.warning(f"Offset strategy failed at page {page}: {str(e)}")
            break
    
    if all_content:
        return all_content
    
    # Strategy 3: Path-based pagination
    logger.info("Trying pagination strategy 3: /page/N")
    for page in range(1, min(max_pages + 1, 6)):
        try:
            url = f"{base_url}/page/{page}"
            content = get_website_text_content(url)
            if content and len(content.strip()) > 100:
                all_content.append(content)
                time.sleep(1)
            else:
                break
        except Exception as e:
            logger.warning(f"Path strategy failed at page {page}: {str(e)}")
            break
    
    if not all_content:
        # Fallback: Just get the main page
        logger.info("All pagination strategies failed, falling back to single page")
        main_content = get_website_text_content(base_url)
        if main_content:
            all_content.append(main_content)
    
    return all_content

def get_latest_data_from_web(data_type: str, team_name: str = None, player_name: str = None, 
                            league: str = "premier_league", max_pages: int = 25) -> pd.DataFrame:
    """
    Get the latest data of a specific type from web sources with pagination support.
    
    Args:
        data_type: Type of data to scrape ('players', 'teams', 'fixtures', 'performance')
        team_name: Optional team name filter
        player_name: Optional player name filter
        league: League name
        max_pages: Maximum number of pages to scrape
        
    Returns:
        DataFrame containing requested data
    """
    try:
        if data_type == 'teams':
            return scrape_team_data(league=league)
        elif data_type == 'players':
            return scrape_player_data(team_name=team_name, league=league, max_pages=max_pages)
        elif data_type == 'fixtures':
            return scrape_fixture_data(league=league)
        elif data_type == 'performance':
            return scrape_performance_data(team_name=team_name, player_name=player_name, league=league)
        else:
            logger.error(f"Unsupported data type: {data_type}")
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error getting latest {data_type} data: {str(e)}")
        return pd.DataFrame()
    
def demonstrate_pagination_scraping(sample_url: str = "https://example-football-site.com/players") -> Dict[str, Any]:
    """
    Demonstrate how the pagination scraping works with a sample URL.
    This function shows how the enhanced scraper handles paginated websites.
    
    Args:
        sample_url: URL to demonstrate pagination scraping
        
    Returns:
        Dictionary with demonstration results
    """
    results = {
        "url_tested": sample_url,
        "pagination_strategies_tried": [],
        "pages_found": 0,
        "total_content_length": 0,
        "players_extracted": 0,
        "success": False
    }
    
    try:
        logger.info(f"Demonstrating pagination scraping on: {sample_url}")
        
        # Try multiple pagination strategies
        strategies = [
            ("Standard page parameter", "?page=N"),
            ("Offset-based pagination", "?offset=N"),
            ("Path-based pagination", "/page/N")
        ]
        
        all_content = scrape_with_multiple_strategies(sample_url, max_pages=5)
        
        if all_content:
            results["success"] = True
            results["pages_found"] = len(all_content)
            results["total_content_length"] = sum(len(content) for content in all_content)
            
            # Try to extract player data
            combined_content = "\n".join(all_content)
            
            # Simple player extraction for demonstration
            player_patterns = re.findall(r'([A-Za-z\s\-\'\.]+)\s+([A-Z]{2,3})\s+([A-Za-z\s]+)', combined_content)
            results["players_extracted"] = len(player_patterns)
            
            logger.info(f"Demonstration successful: {results['pages_found']} pages, {results['players_extracted']} players found")
        else:
            logger.warning("Demonstration failed: No content could be scraped")
            
    except Exception as e:
        logger.error(f"Error in pagination demonstration: {str(e)}")
        results["error"] = str(e)
    
    return results