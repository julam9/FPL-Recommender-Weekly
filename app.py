import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_manager import load_data, save_data, update_player_availability, fetch_specific_data
from src.player_evaluation import rank_players_by_position, calculate_player_performance
from src.team_optimizer import build_optimal_team, select_substitutes
from src.opponent_analyzer import get_opponent_strength
from src.performance_tracker import evaluate_team_performance, record_performance
from src.budget_calculator import calculate_remaining_budget, calculate_player_value
from src.utils import get_current_gameweek, positions_required

# Check if web scraper is available
try:
    from src.web_scraper import get_website_text_content
    WEB_SCRAPER_AVAILABLE = True
except ImportError:
    WEB_SCRAPER_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Football Team Recommendation System",
    page_icon="⚽",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'budget' not in st.session_state:
    st.session_state.budget = 100.0  # Default budget in millions
if 'squad' not in st.session_state:
    st.session_state.squad = []
if 'starting_xi' not in st.session_state:
    st.session_state.starting_xi = []
if 'substitutes' not in st.session_state:
    st.session_state.substitutes = []
if 'manager' not in st.session_state:
    st.session_state.manager = None
if 'gameweek' not in st.session_state:
    st.session_state.gameweek = get_current_gameweek()
if 'team_performance_history' not in st.session_state:
    st.session_state.team_performance_history = []
if 'last_data_update' not in st.session_state:
    st.session_state.last_data_update = None

# Title and header
st.title("⚽ Football Team Recommendation System")
st.markdown("Build your optimal team based on performance, budget, and opponent analysis")

# Sidebar for navigation and settings
with st.sidebar:
    st.header("Settings & Navigation")
    
    # Budget setting
    budget = st.number_input("Budget (in millions)", min_value=50.0, max_value=200.0, value=st.session_state.budget, step=1.0)
    if budget != st.session_state.budget:
        st.session_state.budget = budget
    
    # Current gameweek selection
    gameweek = st.slider("Current Gameweek", min_value=1, max_value=38, value=st.session_state.gameweek)
    if gameweek != st.session_state.gameweek:
        st.session_state.gameweek = gameweek
    
    # Navigation
    page = st.radio("Navigation", [
        "Team Builder", 
        "Player Database", 
        "Performance Analysis", 
        "Weekly Recommendations",
        "Budget Analysis",
        "Data Manager"
    ])
    
    st.markdown("---")
    st.markdown(f"**Remaining Budget:** £{calculate_remaining_budget(st.session_state.squad, st.session_state.budget):.2f}M")

# Load data
players_df, teams_df, fixtures_df, performance_history_df = load_data(st.session_state.gameweek)

# Main content based on selected page
if page == "Team Builder":
    st.header("Team Builder")
    
    # Display current team if it exists
    if st.session_state.squad:
        st.subheader("Current Squad")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Starting XI**")
            if st.session_state.starting_xi:
                starting_df = pd.DataFrame(st.session_state.starting_xi)
                st.dataframe(starting_df[['name', 'position', 'team', 'price', 'performance_score']])
            else:
                st.info("No starting XI selected yet")
        
        with col2:
            st.write("**Substitutes**")
            if st.session_state.substitutes:
                subs_df = pd.DataFrame(st.session_state.substitutes)
                st.dataframe(subs_df[['name', 'position', 'team', 'price', 'performance_score']])
            else:
                st.info("No substitutes selected yet")
        
        st.write("**Manager**")
        if st.session_state.manager:
            st.write(f"{st.session_state.manager['name']} ({st.session_state.manager['team']})")
        else:
            st.info("No manager selected yet")
            
        # Team actions
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Reset Squad"):
                st.session_state.squad = []
                st.session_state.starting_xi = []
                st.session_state.substitutes = []
                st.session_state.manager = None
                st.rerun()
        
        with col2:
            if st.button("Save Squad"):
                save_data(st.session_state.squad, st.session_state.manager, st.session_state.gameweek)
                st.success("Squad saved successfully!")
    
    # Build team options
    st.markdown("---")
    st.subheader("Build Team")
    
    build_method = st.radio("Build Method", ["Auto-generate Team", "Manual Selection"])
    
    if build_method == "Auto-generate Team":
        st.markdown("Generate an optimal team based on performance, budget, and opponent analysis")
        
        # Options for team generation
        col1, col2 = st.columns(2)
        
        with col1:
            performance_weight = st.slider("Performance Weight", 0.0, 1.0, 0.7, 0.1)
            budget_weight = st.slider("Budget Weight", 0.0, 1.0, 0.3, 0.1)
        
        with col2:
            consider_opponents = st.checkbox("Consider Opponent Strength", value=True)
            prioritize_form = st.checkbox("Prioritize Current Form", value=True)
        
        if st.button("Generate Optimal Team"):
            with st.spinner("Building optimal team..."):
                # Get next opponent for each team
                next_opponents = {}
                for _, team in teams_df.iterrows():
                    next_opponents[team['name']] = get_opponent_strength(team['name'], st.session_state.gameweek, fixtures_df, teams_df)
                
                # Build optimal starting XI
                st.session_state.starting_xi = build_optimal_team(
                    players_df, 
                    budget=st.session_state.budget * 0.8,  # Allocate 80% of budget to starting XI
                    performance_weight=performance_weight,
                    budget_weight=budget_weight,
                    consider_opponents=consider_opponents,
                    next_opponents=next_opponents,
                    prioritize_form=prioritize_form
                )
                
                # Get available players for substitutes (excluding starting XI)
                available_players = players_df[~players_df['player_id'].isin([p['player_id'] for p in st.session_state.starting_xi])]
                
                # Select substitutes
                st.session_state.substitutes = select_substitutes(
                    available_players,
                    budget=st.session_state.budget * 0.2,  # Allocate 20% of budget to substitutes
                    current_squad=st.session_state.starting_xi,
                    performance_weight=performance_weight,
                    budget_weight=budget_weight
                )
                
                # Combine starting XI and substitutes to form the squad
                st.session_state.squad = st.session_state.starting_xi + st.session_state.substitutes
                
                # Select a manager (highest-rated available)
                if not teams_df.empty:
                    top_manager = teams_df.sort_values('manager_rating', ascending=False).iloc[0]
                    st.session_state.manager = {
                        'name': top_manager['manager_name'],
                        'team': top_manager['name'],
                        'rating': top_manager['manager_rating']
                    }
                
                st.success("Team generated successfully!")
                # st.rerun()
    
    else:  # Manual Selection
        st.markdown("Manually select players for your team")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            position_filter = st.selectbox("Filter by Position", ["All"] + list(positions_required.keys()))
        
        with col2:
            team_filter = st.selectbox("Filter by Team", ["All"] + sorted(players_df['team'].unique().tolist()))
        
        with col3:
            price_range = st.slider("Price Range (in millions)", 
                                  min_value=float(players_df['price'].min()), 
                                  max_value=float(players_df['price'].max()), 
                                  value=(float(players_df['price'].min()), float(players_df['price'].max())))
        
        # Apply filters
        filtered_df = players_df.copy()
        
        if position_filter != "All":
            filtered_df = filtered_df[filtered_df['position'] == position_filter]
        
        if team_filter != "All":
            filtered_df = filtered_df[filtered_df['team'] == team_filter]
        
        filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & 
                                (filtered_df['price'] <= price_range[1])]
        
        # Display available players
        st.dataframe(
            filtered_df[['name', 'position', 'team', 'price', 'performance_score', 'form', 'is_available']],
            use_container_width=True
        )
        
        # Add player to squad
        st.markdown("---")
        st.subheader("Add Player to Squad")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_player_id = st.selectbox(
                "Select Player", 
                filtered_df['player_id'].tolist(),
                format_func=lambda x: filtered_df.loc[filtered_df['player_id'] == x, 'name'].values[0]
            )
        
        with col2:
            squad_role = st.radio("Squad Role", ["Starting XI", "Substitute"])
        
        if st.button("Add to Squad"):
            # Check if player already in squad
            if any(p.get('player_id') == selected_player_id for p in st.session_state.squad):
                st.error("This player is already in your squad!")
            else:
                # Get player details
                player_details = filtered_df[filtered_df['player_id'] == selected_player_id].iloc[0].to_dict()
                player_dict = {
                    'player_id': player_details['player_id'],
                    'name': player_details['name'],
                    'position': player_details['position'],
                    'team': player_details['team'],
                    'price': player_details['price'],
                    'performance_score': player_details['performance_score'],
                    'form': player_details['form']
                }
                
                # Check budget
                remaining_budget = calculate_remaining_budget(st.session_state.squad, st.session_state.budget)
                if player_dict['price'] > remaining_budget:
                    st.error(f"Not enough budget! Remaining budget: £{remaining_budget:.2f}M")
                else:
                    # Check position limits
                    current_positions = [p['position'] for p in st.session_state.squad]
                    position = player_dict['position']
                    
                    # Count current players in this position
                    position_count = current_positions.count(position)
                    
                    if position_count >= positions_required.get(position, 0):
                        st.error(f"You already have the maximum number of {position} players!")
                    else:
                        # Add player to squad
                        if squad_role == "Starting XI":
                            st.session_state.starting_xi.append(player_dict)
                        else:
                            st.session_state.substitutes.append(player_dict)
                        
                        st.session_state.squad = st.session_state.starting_xi + st.session_state.substitutes
                        st.success(f"Added {player_dict['name']} to squad!")
                        #  st.rerun()
        
        # Manager selection
        st.markdown("---")
        st.subheader("Select Manager")
        
        selected_manager = st.selectbox(
            "Manager", 
            teams_df['manager_name'].tolist(),
            format_func=lambda x: f"{x} ({teams_df.loc[teams_df['manager_name'] == x, 'name'].values[0]})"
        )
        
        if st.button("Select Manager"):
            manager_team = teams_df.loc[teams_df['manager_name'] == selected_manager, 'name'].values[0]
            manager_rating = teams_df.loc[teams_df['manager_name'] == selected_manager, 'manager_rating'].values[0]
            
            st.session_state.manager = {
                'name': selected_manager,
                'team': manager_team,
                'rating': manager_rating
            }
            
            st.success(f"Selected {selected_manager} as manager!")
            # st.rerun()

elif page == "Player Database":
    st.header("Player Database")
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        position_filter = st.selectbox("Position", ["All"] + list(positions_required.keys()))
    
    with col2:
        team_filter = st.selectbox("Team", ["All"] + sorted(players_df['team'].unique().tolist()))
    
    with col3:
        availability_filter = st.selectbox("Availability", ["All", "Available", "Unavailable"])
    
    search_query = st.text_input("Search by player name")
    
    # Apply filters
    filtered_df = players_df.copy()
    
    if position_filter != "All":
        filtered_df = filtered_df[filtered_df['position'] == position_filter]
    
    if team_filter != "All":
        filtered_df = filtered_df[filtered_df['team'] == team_filter]
    
    if availability_filter == "Available":
        filtered_df = filtered_df[filtered_df['is_available'] == True]
    elif availability_filter == "Unavailable":
        filtered_df = filtered_df[filtered_df['is_available'] == False]
    
    if search_query:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False)]
    
    # Sort options
    sort_by = st.selectbox(
        "Sort By", 
        ["performance_score", "price", "form", "goals", "assists", "clean_sheets"]
    )
    sort_order = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True)
    
    ascending = sort_order == "Ascending"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
    
    # Display players
    st.dataframe(filtered_df.drop(['player_id', 'unavailability_reason'], axis=1), use_container_width=True)
    
    # Update player availability
    st.markdown("---")
    st.subheader("Update Player Availability")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        player_to_update = st.selectbox(
            "Select Player", 
            players_df['player_id'].tolist(),
            format_func=lambda x: players_df.loc[players_df['player_id'] == x, 'name'].values[0]
        )
    
    with col2:
        availability_status = st.radio("Availability Status", ["Available", "Unavailable"])
    
    with col3:
        if availability_status == "Unavailable":
            reason = st.selectbox("Reason", ["Injury", "Suspension", "Personal Reasons", "Not Selected", "Other"])
        else:
            reason = None
    
    if st.button("Update Availability"):
        is_available = availability_status == "Available"
        update_player_availability(player_to_update, is_available, reason)
        st.success("Player availability updated!")
        #  st.rerun()
    
    # Player performance visualization
    st.markdown("---")
    st.subheader("Player Performance Trends")
    
    selected_player = st.selectbox(
        "Select Player for Performance Analysis",
        players_df['player_id'].tolist(),
        format_func=lambda x: players_df.loc[players_df['player_id'] == x, 'name'].values[0]
    )
    
    selected_player_name = players_df.loc[players_df['player_id'] == selected_player, 'name'].values[0]
    
    # Get performance history for selected player
    player_history = performance_history_df[performance_history_df['player_id'] == selected_player]
    
    if not player_history.empty:
        # Plot performance trend
        fig = px.line(
            player_history, 
            x='gameweek', 
            y='performance_score',
            title=f"{selected_player_name}'s Performance Over Season"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fig = px.line(player_history, x='gameweek', y='goals', title="Goals")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(player_history, x='gameweek', y='assists', title="Assists")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            if 'GK' in player_history['position'].values[0] or 'CB' in player_history['position'].values[0] or 'RB' in player_history['position'].values[0] or 'LB' in player_history['position'].values[0]:
                fig = px.line(player_history, x='gameweek', y='clean_sheets', title="Clean Sheets")
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.line(player_history, x='gameweek', y='key_passes', title="Key Passes")
                st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            fig = px.line(player_history, x='gameweek', y='minutes_played', title="Minutes Played")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No performance history available for {selected_player_name}")

elif page == "Performance Analysis":
    st.header("Performance Analysis")
    
    if not st.session_state.team_performance_history:
        st.info("No team performance data available yet. Build a team and compete in gameweeks to see performance analysis.")
    else:
        # Overall team performance over gameweeks
        performance_df = pd.DataFrame(st.session_state.team_performance_history)
        
        st.subheader("Team Performance Trend")
        fig = px.line(
            performance_df, 
            x='gameweek', 
            y='total_points',
            title="Team Points Over Season"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Position-based performance
        st.subheader("Performance by Position")
        
        if not performance_df.empty:
            position_data = []
            for week in performance_df['gameweek'].unique():
                week_data = performance_df[performance_df['gameweek'] == week]
                if not week_data.empty and 'position_points' in week_data.iloc[0]:
                    position_points = week_data.iloc[0]['position_points']
                    for pos, points in position_points.items():
                        position_data.append({
                            'gameweek': week,
                            'position': pos,
                            'points': points
                        })
            
            if position_data:
                position_df = pd.DataFrame(position_data)
                fig = px.line(
                    position_df, 
                    x='gameweek', 
                    y='points', 
                    color='position',
                    title="Points by Position Over Season"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No position-based performance data available")
        
        # Compare predicted vs actual performance
        st.subheader("Predicted vs Actual Performance")
        
        if 'predicted_points' in performance_df.columns and 'total_points' in performance_df.columns:
            fig = px.scatter(
                performance_df,
                x='predicted_points',
                y='total_points',
                hover_name='gameweek',
                title="Predicted vs Actual Points"
            )
            # Add 45-degree line
            fig.add_shape(
                type='line',
                x0=performance_df['predicted_points'].min(),
                y0=performance_df['predicted_points'].min(),
                x1=performance_df['predicted_points'].max(),
                y1=performance_df['predicted_points'].max(),
                line=dict(color='red', dash='dash')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate prediction accuracy
            performance_df['prediction_error'] = performance_df['predicted_points'] - performance_df['total_points']
            performance_df['abs_error'] = performance_df['prediction_error'].abs()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Prediction Error", f"{performance_df['prediction_error'].mean():.2f} pts")
            
            with col2:
                st.metric("Prediction Accuracy", f"{(1 - performance_df['abs_error'].mean() / performance_df['total_points'].mean()) * 100:.1f}%")
            
            with col3:
                st.metric("Best Prediction", f"GW {performance_df.loc[performance_df['abs_error'].idxmin(), 'gameweek']}")
        else:
            st.info("No prediction comparison data available")
        
        # Player contribution to team
        st.subheader("Top Player Contributions")
        
        top_players_data = []
        for week in performance_df['gameweek'].unique():
            week_data = performance_df[performance_df['gameweek'] == week]
            if not week_data.empty and 'player_points' in week_data.iloc[0]:
                player_points = week_data.iloc[0]['player_points']
                for player, points in player_points.items():
                    top_players_data.append({
                        'gameweek': week,
                        'player': player,
                        'points': points
                    })
        
        if top_players_data:
            top_players_df = pd.DataFrame(top_players_data)
            
            # Get top 5 players by total points
            top5_players = top_players_df.groupby('player')['points'].sum().nlargest(5).index.tolist()
            
            # Filter data for top 5 players
            top5_df = top_players_df[top_players_df['player'].isin(top5_players)]
            
            fig = px.bar(
                top5_df.groupby('player')['points'].sum().reset_index().sort_values('points', ascending=False),
                x='player',
                y='points',
                title="Top 5 Players by Total Points"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Player consistency (standard deviation of points)
            player_consistency = top_players_df.groupby('player').agg(
                avg_points=('points', 'mean'),
                std_points=('points', 'std'),
                total_points=('points', 'sum')
            ).reset_index()
            
            player_consistency['consistency'] = 1 / (1 + player_consistency['std_points'])
            player_consistency = player_consistency.sort_values('total_points', ascending=False).head(10)
            
            fig = px.scatter(
                player_consistency,
                x='avg_points',
                y='consistency',
                size='total_points',
                hover_name='player',
                title="Player Performance Consistency vs Average Points (Top 10)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No player contribution data available")

elif page == "Weekly Recommendations":
    st.header("Weekly Recommendations")
    
    # Current gameweek info
    st.subheader(f"Gameweek {st.session_state.gameweek} Recommendations")
    
    # Previous performance summary if available
    if st.session_state.gameweek > 1 and st.session_state.team_performance_history:
        prev_performances = [p for p in st.session_state.team_performance_history if p['gameweek'] == st.session_state.gameweek - 1]
        
        if prev_performances:
            prev_performance = prev_performances[0]
            st.markdown("### Previous Gameweek Performance")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Points", prev_performance.get('total_points', 0))
            
            with col2:
                st.metric("Rank Change", prev_performance.get('rank_change', 0), 
                        delta_color="normal" if prev_performance.get('rank_change', 0) <= 0 else "inverse")
            
            with col3:
                predicted = prev_performance.get('predicted_points', 0)
                actual = prev_performance.get('total_points', 0)
                performance_diff = actual - predicted
                st.metric("vs Prediction", f"{actual} vs {predicted}", 
                        delta=performance_diff, 
                        delta_color="normal" if performance_diff >= 0 else "inverse")
            
            # Areas for improvement
            if 'areas_for_improvement' in prev_performance:
                st.markdown("#### Areas for Improvement")
                for area in prev_performance['areas_for_improvement']:
                    st.markdown(f"- {area}")
    
    # Next opponent analysis
    st.markdown("---")
    st.subheader("Upcoming Opponent Analysis")
    
    if st.session_state.squad:
        # Get unique teams in squad
        squad_teams = set([player['team'] for player in st.session_state.squad])
        
        # Get next opponents
        opponents_data = []
        for team in squad_teams:
            opponent_info = get_opponent_strength(team, st.session_state.gameweek, fixtures_df, teams_df)
            if opponent_info:
                opponents_data.append({
                    'team': team,
                    'opponent': opponent_info['opponent'],
                    'is_home': opponent_info['is_home'],
                    'opponent_strength': opponent_info['strength'],
                    'expected_difficulty': opponent_info['expected_difficulty']
                })
        
        if opponents_data:
            opponents_df = pd.DataFrame(opponents_data)
            opponents_df['match'] = opponents_df.apply(
                lambda x: f"{x['team']} {'vs' if x['is_home'] else '@'} {x['opponent']}", 
                axis=1
            )
            
            # Display matches
            fig = px.bar(
                opponents_df.sort_values('expected_difficulty'),
                x='match',
                y='expected_difficulty',
                color='expected_difficulty',
                color_continuous_scale='RdYlGn_r',
                title="Fixture Difficulty for Your Players' Teams"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display players based on fixture difficulty
            if st.session_state.squad:
                squad_df = pd.DataFrame(st.session_state.squad)
                
                # Merge with opponent data
                squad_with_fixtures = pd.merge(
                    squad_df,
                    opponents_df[['team', 'opponent', 'is_home', 'expected_difficulty']],
                    on='team',
                    how='left'
                )
                
                st.markdown("### Player Recommendations Based on Fixtures")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Players with Favorable Fixtures")
                    favorable = squad_with_fixtures[squad_with_fixtures['expected_difficulty'] <= 3].sort_values('expected_difficulty')
                    if not favorable.empty:
                        st.dataframe(favorable[['name', 'position', 'team', 'opponent', 'is_home', 'expected_difficulty']])
                    else:
                        st.info("No players with favorable fixtures found")
                
                with col2:
                    st.markdown("#### Players with Difficult Fixtures")
                    difficult = squad_with_fixtures[squad_with_fixtures['expected_difficulty'] >= 4].sort_values('expected_difficulty', ascending=False)
                    if not difficult.empty:
                        st.dataframe(difficult[['name', 'position', 'team', 'opponent', 'is_home', 'expected_difficulty']])
                    else:
                        st.info("No players with difficult fixtures found")
        else:
            st.info("No fixture data available for analysis")
    else:
        st.info("Build a team first to see opponent analysis")
    
    # Player recommendations
    st.markdown("---")
    st.subheader("Player Recommendations")
    
    # Get top performers by position
    top_performers = {}
    for position in positions_required.keys():
        position_players = players_df[players_df['position'] == position]
        if not position_players.empty:
            # Rank players by position
            ranked_players = rank_players_by_position(position_players, st.session_state.gameweek)
            top_performers[position] = ranked_players.head(5)
    
    if top_performers:
        tab_positions = st.tabs(list(top_performers.keys()))
        
        for i, position in enumerate(top_performers.keys()):
            with tab_positions[i]:
                st.dataframe(
                    top_performers[position][['name', 'team', 'price', 'performance_score', 'form']],
                    use_container_width=True
                )
    else:
        st.info("No player data available for recommendations")
    
    # Team optimization suggestions
    st.markdown("---")
    st.subheader("Team Optimization Suggestions")
    
    if st.session_state.squad:
        squad_df = pd.DataFrame(st.session_state.squad)
        
        # Identify underperforming players
        underperforming = squad_df[squad_df['form'] < squad_df['form'].median()]
        
        # Identify potential replacements
        replacements = {}
        for _, player in underperforming.iterrows():
            position = player['position']
            price = player['price'] * 1.1  # Allow 10% more budget for replacement
            
            # Find potential replacements with better form
            candidates = players_df[
                (players_df['position'] == position) & 
                (players_df['price'] <= price) & 
                (players_df['form'] > player['form']) &
                (players_df['is_available'] == True)
            ].sort_values('form', ascending=False).head(3)
            
            if not candidates.empty:
                replacements[player['name']] = candidates
        
        if replacements:
            st.markdown("### Suggested Player Replacements")
            
            for player_name, candidates in replacements.items():
                st.markdown(f"**{player_name}** could be replaced by:")
                st.dataframe(candidates[['name', 'team', 'price', 'performance_score', 'form']])
        else:
            st.success("Your team looks optimized! No obvious replacements needed.")
    else:
        st.info("Build a team first to see optimization suggestions")
    
    # Record performance for current gameweek
    st.markdown("---")
    st.subheader("Record Team Performance")
    
    if st.session_state.squad:
        with st.form("performance_form"):
            st.markdown(f"Record performance for Gameweek {st.session_state.gameweek}")
            
            # Player performance inputs
            st.markdown("### Player Points")
            
            player_points = {}
            cols = st.columns(3)
            for i, player in enumerate(st.session_state.squad):
                col_idx = i % 3
                with cols[col_idx]:
                    player_points[player['name']] = st.number_input(
                        f"{player['name']} ({player['position']})", 
                        min_value=0, 
                        max_value=20, 
                        value=0
                    )
            
            # Team performance metrics
            st.markdown("### Team Performance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_points = st.number_input("Total Team Points", min_value=0, max_value=150, value=sum(player_points.values()))
                team_rank = st.number_input("Overall Rank", min_value=1, value=1000000)
            
            with col2:
                prev_rank = 1000000  # Default value
                if st.session_state.team_performance_history:
                    prev_performance = max(st.session_state.team_performance_history, key=lambda x: x['gameweek'])
                    if 'team_rank' in prev_performance:
                        prev_rank = prev_performance['team_rank']
                
                rank_change = st.number_input("Rank Change", value=prev_rank - team_rank)
                notes = st.text_area("Performance Notes", "")
            
            submit_button = st.form_submit_button("Record Performance")
            
            if submit_button:
                # Calculate position-based points
                position_points = {}
                for player in st.session_state.squad:
                    position = player['position']
                    if position not in position_points:
                        position_points[position] = 0
                    position_points[position] += player_points[player['name']]
                
                # Generate areas for improvement
                areas_for_improvement = []
                
                # Check underperforming positions
                avg_pos_points = sum(position_points.values()) / len(position_points)
                for pos, points in position_points.items():
                    if points < avg_pos_points * 0.8:  # 20% below average
                        areas_for_improvement.append(f"Consider strengthening {pos} position - only {points} points vs. {avg_pos_points:.1f} average")
                
                # Check if team performance was below expected
                expected_points = sum([p['performance_score'] for p in st.session_state.squad]) / 2  # Rough estimate
                if total_points < expected_points * 0.8:  # 20% below expected
                    areas_for_improvement.append(f"Team underperformed vs. expectations ({total_points} vs. {expected_points:.1f} expected)")
                
                # Record performance
                performance_data = {
                    'gameweek': st.session_state.gameweek,
                    'total_points': total_points,
                    'team_rank': team_rank,
                    'rank_change': rank_change,
                    'player_points': player_points,
                    'position_points': position_points,
                    'predicted_points': expected_points,
                    'areas_for_improvement': areas_for_improvement,
                    'notes': notes,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                record_performance(performance_data, st.session_state.gameweek)
                st.session_state.team_performance_history.append(performance_data)
                
                st.success(f"Performance for Gameweek {st.session_state.gameweek} recorded!")
    else:
        st.info("Build a team first to record performance")

elif page == "Budget Analysis":
    st.header("Budget Analysis")
    
    if st.session_state.squad:
        squad_df = pd.DataFrame(st.session_state.squad)
        
        # Calculate total and remaining budget
        total_budget = st.session_state.budget
        spent_budget = squad_df['price'].sum()
        remaining_budget = total_budget - spent_budget
        
        # Budget overview
        st.subheader("Budget Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Budget", f"£{total_budget:.2f}M")
        
        with col2:
            st.metric("Spent", f"£{spent_budget:.2f}M", f"{spent_budget / total_budget * 100:.1f}%")
        
        with col3:
            st.metric("Remaining", f"£{remaining_budget:.2f}M", f"{remaining_budget / total_budget * 100:.1f}%")
        
        # Budget allocation by position
        st.subheader("Budget Allocation by Position")
        
        position_budget = squad_df.groupby('position')['price'].sum().reset_index()
        position_budget['percentage'] = position_budget['price'] / spent_budget * 100
        
        fig = px.pie(
            position_budget,
            values='price',
            names='position',
            title="Budget Allocation by Position",
            hover_data=['percentage'],
            labels={'percentage': 'Percentage of Budget'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Budget efficiency analysis
        st.subheader("Budget Efficiency Analysis")
        
        # Calculate performance per million spent
        squad_df['value'] = squad_df['performance_score'] / squad_df['price']
        
        # Sort by value
        value_df = squad_df.sort_values('value', ascending=False)
        
        # Plot value analysis
        fig = px.scatter(
            value_df,
            x='price',
            y='performance_score',
            size='value',
            color='position',
            hover_name='name',
            title="Player Value Analysis (Performance Score per Million Spent)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top value players
        st.markdown("### Best Value Players")
        st.dataframe(
            value_df[['name', 'position', 'team', 'price', 'performance_score', 'value']].head(5),
            use_container_width=True
        )
        
        # Least value players
        st.markdown("### Least Value Players")
        st.dataframe(
            value_df[['name', 'position', 'team', 'price', 'performance_score', 'value']].tail(5),
            use_container_width=True
        )
        
        # Budget reallocation recommendations
        st.subheader("Budget Reallocation Recommendations")
        
        # Find positions with poor value
        position_value = squad_df.groupby('position').agg(
            avg_value=('value', 'mean'),
            total_budget=('price', 'sum')
        ).reset_index()
        
        poor_value_positions = position_value[position_value['avg_value'] < position_value['avg_value'].median()]
        good_value_positions = position_value[position_value['avg_value'] > position_value['avg_value'].median()]
        
        if not poor_value_positions.empty and not good_value_positions.empty:
            st.markdown("### Suggested Budget Adjustments")
            
            for _, pos in poor_value_positions.iterrows():
                target_pos = good_value_positions.iloc[0]['position']
                reallocation_amount = pos['total_budget'] * 0.2  # Suggest reallocating 20% of budget
                
                st.markdown(f"- Consider moving £{reallocation_amount:.2f}M from **{pos['position']}** to **{target_pos}** for better value")
        else:
            st.success("Budget allocation looks balanced across positions!")
        
        # Market value analysis
        st.subheader("Market Value Analysis")
        
        # Plot price distribution
        fig = px.histogram(
            players_df,
            x='price',
            color='position',
            nbins=20,
            title="Player Price Distribution in Market"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Price range analysis
        price_ranges = [
            {'name': 'Budget', 'min': 0, 'max': 5},
            {'name': 'Mid-range', 'min': 5, 'max': 9},
            {'name': 'Premium', 'min': 9, 'max': 15},
            {'name': 'Elite', 'min': 15, 'max': 20}
        ]
        
        squad_distribution = []
        for price_range in price_ranges:
            count = len(squad_df[(squad_df['price'] >= price_range['min']) & (squad_df['price'] < price_range['max'])])
            squad_distribution.append({
                'range': price_range['name'],
                'count': count,
                'percentage': count / len(squad_df) * 100
            })
        
        squad_distribution_df = pd.DataFrame(squad_distribution)
        
        fig = px.bar(
            squad_distribution_df,
            x='range',
            y='count',
            title="Squad Distribution by Price Range",
            text='percentage',
            labels={'percentage': '% of Squad'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Build a team first to see budget analysis")

elif page == "Data Manager":
    st.header("Data Manager & Web Scraper")
    
    # Display last update information
    if st.session_state.last_data_update:
        st.success(f"Last data update: {st.session_state.last_data_update}")
    
    # Check if web scraper is available
    if not WEB_SCRAPER_AVAILABLE:
        st.error("Web scraper is not available. Please make sure trafilatura is installed.")
    else:
        st.success("Web scraper is available and ready to use.")
        
        st.subheader("Fetch Data from Web")
        
        # Section for fetching specific data types
        st.write("### Update Specific Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_type = st.selectbox(
                "Select data type to fetch", 
                ["players", "teams", "fixtures", "performance"]
            )
            
            league = st.selectbox(
                "Select league",
                ["premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"]
            )
        
        with col2:
            team_filter = st.text_input("Team name filter (optional)")
            player_filter = st.text_input("Player name filter (optional)")
        
        if st.button("Fetch Selected Data"):
            with st.spinner(f"Fetching {data_type} data from web..."):
                # Create filters
                team_name = team_filter if team_filter else None
                player_name = player_filter if player_filter else None
                
                # Fetch data
                result_df = fetch_specific_data(
                    data_type=data_type,
                    team_name=team_name,
                    player_name=player_name,
                    league=league
                )
                
                if result_df is not None and not result_df.empty:
                    # Update the timestamp
                    st.session_state.last_data_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success(f"Successfully fetched {len(result_df)} {data_type} records!")
                    st.dataframe(result_df)
                else:
                    st.error(f"No {data_type} data found or error occurred during fetching.")
        
        # Section for direct web text extraction
        st.write("### Extract Text from Website")
        
        website_url = st.text_input("Enter website URL to extract content from")
        
        if st.button("Extract Content") and website_url:
            with st.spinner("Extracting content from website..."):
                try:
                    content = get_website_text_content(website_url)
                    if content:
                        st.success("Content extracted successfully!")
                        
                        with st.expander("View extracted content", expanded=False):
                            st.text_area("Content", content, height=300)
                            
                        # Option to save content
                        if st.button("Save to file"):
                            file_name = f"data/extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                            os.makedirs(os.path.dirname(file_name), exist_ok=True)
                            with open(file_name, "w") as f:
                                f.write(content)
                            st.success(f"Content saved to {file_name}")
                    else:
                        st.error("Failed to extract content from the website.")
                except Exception as e:
                    st.error(f"Error extracting content: {str(e)}")
        
        # Section for updating all data
        st.write("### Update All Data")
        
        update_league = st.selectbox(
            "Select league for full update",
            ["premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"],
            key="update_all_league"
        )
        
        if st.button("Update All Data"):
            with st.spinner("Updating all data from web sources..."):
                try:
                    players_df, teams_df, fixtures_df, performance_history_df = load_data(
                        current_gameweek=st.session_state.gameweek,
                        use_web_data=True,
                        league=update_league
                    )
                    
                    # Update the timestamp
                    st.session_state.last_data_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if (not players_df.empty and not teams_df.empty and 
                        not fixtures_df.empty and not performance_history_df.empty):
                        st.success(f"All data successfully updated from web sources! Last update: {st.session_state.last_data_update}")
                        
                        st.write(f"Players: {len(players_df)} records")
                        st.write(f"Teams: {len(teams_df)} records")
                        st.write(f"Fixtures: {len(fixtures_df)} records")
                        st.write(f"Performance History: {len(performance_history_df)} records")
                    else:
                        st.warning("Some data could not be updated. Check logs for details.")
                except Exception as e:
                    st.error(f"Error updating data: {str(e)}")
    
    # Data Management Section
    st.subheader("Manage Existing Data")
    
    # Load current data
    players_df, teams_df, fixtures_df, performance_history_df = load_data(st.session_state.gameweek)
    
    data_files = {
        "Players": (players_df, "players.csv"),
        "Teams": (teams_df, "teams.csv"),
        "Fixtures": (fixtures_df, "fixtures.csv"),
        "Performance History": (performance_history_df, "performance_history.csv")
    }
    
    selected_data = st.selectbox("Select data to view/edit", list(data_files.keys()))
    
    df, filename = data_files[selected_data]
    
    st.write(f"### {selected_data} Data")
    st.dataframe(df)
    
    st.write(f"Total records: {len(df)}")
    
    # Export options
    if st.button(f"Export {selected_data} to CSV"):
        export_path = f"data/export_{filename}"
        df.to_csv(export_path, index=False)
        st.success(f"Data exported to {export_path}")
    
    # Import options
    st.write("### Import Data")
    st.write("Upload a CSV file to replace current data (use with caution)")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        try:
            imported_df = pd.read_csv(uploaded_file)
            if st.button("Import Data"):
                imported_df.to_csv(f"data/{filename}", index=False)
                
                # Update the timestamp
                st.session_state.last_data_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.success(f"Data imported successfully! Replaced {filename} with new data.")
                st.info("Please refresh the page to see the updated data.")
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
