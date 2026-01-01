from typing import List, Dict, Any


def calculate_remaining_budget(squad: List[Dict[str, Any]], total_budget: float) -> float:
    """
    Calculate the remaining budget after squad selection
    
    Args:
        squad: List of player dictionaries in the squad
        total_budget: Total available budget
        
    Returns:
        Remaining budget
    """
    # Calculate total cost of current squad
    if not squad:
        return total_budget
    
    squad_cost = sum(player['price'] for player in squad)
    remaining = total_budget - squad_cost
    
    # Ensure we don't return a negative value
    return max(0, remaining)


def calculate_squad_value(squad: List[Dict[str, Any]]) -> float:
    """
    Calculate the total market value of the squad
    
    Args:
        squad: List of player dictionaries in the squad
        
    Returns:
        Total squad value
    """
    if not squad:
        return 0
    
    return sum(player['price'] for player in squad)


def calculate_player_value(player: Dict[str, Any]) -> float:
    """
    Calculate the value (performance per million) of a player
    
    Args:
        player: Dictionary containing player information
        
    Returns:
        Value metric (performance per million)
    """
    if player['price'] <= 0:
        return 0
    
    return player['performance_score'] / player['price']


def calculate_budget_allocation(squad: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate budget allocation by position
    
    Args:
        squad: List of player dictionaries in the squad
        
    Returns:
        Dictionary mapping positions to budget allocation percentages
    """
    if not squad:
        return {}
    
    # Group budget by position
    position_budget = {}
    total_budget = 0
    
    for player in squad:
        position = player['position']
        price = player['price']
        
        if position not in position_budget:
            position_budget[position] = 0
        
        position_budget[position] += price
        total_budget += price
    
    # Calculate percentages
    budget_percentages = {}
    for position, budget in position_budget.items():
        budget_percentages[position] = (budget / total_budget) * 100 if total_budget > 0 else 0
    
    return budget_percentages


def calculate_budget_efficiency(squad: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate budget efficiency metrics for the squad
    
    Args:
        squad: List of player dictionaries in the squad
        
    Returns:
        Dictionary containing budget efficiency metrics
    """
    if not squad:
        return {
            'avg_value': 0,
            'best_value_player': None,
            'worst_value_player': None,
            'position_value': {}
        }
    
    # Calculate value for each player
    for player in squad:
        player['value'] = calculate_player_value(player)
    
    # Calculate average value
    avg_value = sum(player['value'] for player in squad) / len(squad)
    
    # Find best and worst value players
    best_value_player = max(squad, key=lambda p: p['value'])
    worst_value_player = min(squad, key=lambda p: p['value'])
    
    # Calculate value by position
    position_values = {}
    position_counts = {}
    
    for player in squad:
        position = player['position']
        value = player['value']
        
        if position not in position_values:
            position_values[position] = 0
            position_counts[position] = 0
        
        position_values[position] += value
        position_counts[position] += 1
    
    # Calculate average value by position
    position_value = {}
    for position, value in position_values.items():
        count = position_counts[position]
        position_value[position] = value / count if count > 0 else 0
    
    return {
        'avg_value': avg_value,
        'best_value_player': best_value_player,
        'worst_value_player': worst_value_player,
        'position_value': position_value
    }


def recommend_budget_adjustments(
    squad: List[Dict[str, Any]], 
    available_players: List[Dict[str, Any]], 
    remaining_budget: float
) -> List[Dict[str, Any]]:
    """
    Recommend budget adjustments to improve squad value
    
    Args:
        squad: List of player dictionaries in the squad
        available_players: List of available players not in the squad
        remaining_budget: Remaining budget
        
    Returns:
        List of recommended adjustments
    """
    if not squad or not available_players:
        return []
    
    # Calculate squad efficiency
    efficiency = calculate_budget_efficiency(squad)
    
    # Find low-value players in the squad
    squad_with_value = [dict(player, value=calculate_player_value(player)) for player in squad]
    low_value_players = sorted(squad_with_value, key=lambda p: p['value'])[:3]
    
    # Find high-value available players
    available_with_value = [dict(player, value=calculate_player_value(player)) for player in available_players]
    high_value_players = sorted(available_with_value, key=lambda p: p['value'], reverse=True)[:10]
    
    # Generate recommendations
    recommendations = []
    
    for low_player in low_value_players:
        # Find potential replacements in the same position
        position = low_player['position']
        position_players = [p for p in high_value_players if p['position'] == position]
        
        for high_player in position_players:
            # Check if we can afford the swap
            price_diff = high_player['price'] - low_player['price']
            
            if price_diff <= remaining_budget:
                # Calculate value improvement
                value_improvement = high_player['value'] - low_player['value']
                
                if value_improvement > 0:
                    recommendations.append({
                        'sell_player': low_player['name'],
                        'buy_player': high_player['name'],
                        'price_diff': price_diff,
                        'value_improvement': value_improvement,
                        'position': position
                    })
    
    # Sort recommendations by value improvement
    recommendations.sort(key=lambda r: r['value_improvement'], reverse=True)
    
    return recommendations[:5]  # Return top 5 recommendations
