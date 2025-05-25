import random
import time
import requests

# Constants and Setup
BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",
    "x-apisports-host": "v3.football.api-sports.io"
}

# Payoff matrix for strategy choices
PAYOFF_MATRIX = {
    ('attack', 'attack'): (0.0186, 0.0042),
    ('attack', 'balance'): (0.0231, 0.0131),
    ('attack', 'defense'): (0.0664, 0.0188),
    ('balance', 'attack'): (0.0012, 0.0213),
    ('balance', 'balance'): (0.0235, 0.0004),
    ('balance', 'defense'): (0.0114, 0.0096),
    ('defense', 'attack'): (0.0036, 0.0683),
    ('defense', 'balance'): (0.0061, 0.0105),
    ('defense', 'defense'): (0.0437, 0.0013)
}

# Style-based strategy probabilities
STYLE_PROBABILITIES = {
    "Counter Attack": (0.45, 0.30, 0.25),
    "Possession Based": (0.30, 0.50, 0.20),
    "High Press": (0.50, 0.30, 0.20),
    "Low Press": (0.20, 0.30, 0.50),
    "Fast Break": (0.50, 0.25, 0.25),
    "Ball Control": (0.30, 0.50, 0.20),
    "Flank Attack": (0.45, 0.35, 0.20),
    "Midfield Control": (0.30, 0.50, 0.20),
    "Direct Play": (0.40, 0.35, 0.25),
    "Territorial": (0.35, 0.45, 0.20),
    "Park The Bus": (0.15, 0.25, 0.60),
    "Gegenpress": (0.50, 0.30, 0.20),
    "Long Ball": (0.40, 0.30, 0.30),
    "Tiki Taka": (0.35, 0.50, 0.15),
    "Defensive Solid": (0.20, 0.35, 0.45),
    "Wing Play": (0.45, 0.35, 0.20),
    "Overload Midfield": (0.30, 0.50, 0.20),
    "Slow Build Up": (0.25, 0.55, 0.20),
    "Direct Counter": (0.50, 0.25, 0.25),
    "Clinical Finishing": (0.50, 0.30, 0.20)
}

# Function to adjust strategy probabilities based on power differences
def adjust_probabilities(base_probs, power_diff):
    attack, balance, defense = base_probs
    
    if power_diff > 3:  # Stronger team increases attack probability
        attack += 0.1
        defense -= 0.05
    elif power_diff < -3:  # Weaker team becomes more defensive
        attack -= 0.1
        defense += 0.05
    
    attack = max(0.1, min(0.6, attack))  # Keep within valid bounds
    defense = max(0.1, min(0.6, defense))
    balance = 1 - attack - defense  # Ensure probabilities sum to 1
    
    return {'attack': attack, 'balance': balance, 'defense': defense}

# Function to simulate a match
def simulate_match(home_team_power, away_team_power, home_style, away_style, minutes_remaining):
    home_base_probs = STYLE_PROBABILITIES.get(home_style, (0.3, 0.4, 0.3))
    away_base_probs = STYLE_PROBABILITIES.get(away_style, (0.3, 0.4, 0.3))
    
    power_diff = home_team_power - away_team_power
    home_strategy_probs = adjust_probabilities(home_base_probs, power_diff)
    away_strategy_probs = adjust_probabilities(away_base_probs, -power_diff)
    
    home_goals, away_goals = 0, 0
    
    for _ in range(minutes_remaining):
        home_choice = random.choices(list(home_strategy_probs.keys()), weights=home_strategy_probs.values())[0]
        away_choice = random.choices(list(away_strategy_probs.keys()), weights=away_strategy_probs.values())[0]
        goal_probs = PAYOFF_MATRIX.get((home_choice, away_choice), (0.0, 0.0))
        
        if random.random() < goal_probs[0]:
            home_goals += 1
        if random.random() < goal_probs[1]:
            away_goals += 1
    
    return home_goals, away_goals

# Fetch current match score
def fetch_current_score(fixture_id):
    url = f"{BASE_URL}/fixtures?id={fixture_id}"
    response = requests.get(url, headers=API_HEADERS)
    
    if response.status_code == 200:
        fixture_data = response.json()
        if "response" in fixture_data:
            fixture = fixture_data["response"][0]
            current_score = fixture.get("goals", {})
            return current_score.get("home", 0), current_score.get("away", 0)
    return 0, 0

# Live simulation function
def live_simulation(fixture_id, home_team_power, away_team_power, home_style, away_style):
    current_minute = 0
    while current_minute < 90:
        home_goals, away_goals = fetch_current_score(fixture_id)
        minutes_remaining = 90 - current_minute
        print(f"Minute {current_minute}: Score: {home_goals}-{away_goals}. Simulating next {minutes_remaining} minutes...")
        
        home_goals_remaining, away_goals_remaining = 0, 0
        for _ in range(100):
            h, a = simulate_match(home_team_power, away_team_power, home_style, away_style, minutes_remaining)
            home_goals_remaining += h
            away_goals_remaining += a
        
        avg_home_goals = home_goals_remaining / 100
        avg_away_goals = away_goals_remaining / 100
        
        print(f"Predicted Final Score: Home {home_goals + avg_home_goals:.1f} - Away {away_goals + avg_away_goals:.1f}")
        
        time.sleep(1 * 1)
        current_minute += 5

# Run the live simulation
fixture_id = 1035037
home_team_power = 1273
away_team_power = 1407
home_style = "Counter Attack"
away_style = "Possession Based"

live_simulation(fixture_id, home_team_power, away_team_power, home_style, away_style)