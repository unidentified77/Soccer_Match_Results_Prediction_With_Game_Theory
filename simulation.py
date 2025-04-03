import pandas as pd
import random
from tactics import determine_team_play_style  # Make sure this is the correct import
from team_power import Team, fill_all_stats
from utils import UnderstatClient

SEASON    = 2024

# Payoff matrix for strategy choices
PAYOFF_MATRIX = {
    ('attack', 'attack'): (0.03, 0.03),
    ('attack', 'balance'): (0.05, 0.02),
    ('attack', 'defense'): (0.07, 0.01),
    ('balance', 'attack'): (0.02, 0.05),
    ('balance', 'balance'): (0.02, 0.02),
    ('balance', 'defense'): (0.04, 0.01),
    ('defense', 'attack'): (0.01, 0.07),
    ('defense', 'balance'): (0.01, 0.04),
    ('defense', 'defense'): (0.01, 0.01)
}

# Style-based base probabilities
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
    "Clinical Finishing": (0.50, 0.30, 0.20),
    "Balanced": (0.33, 0.33, 0.33)
}

def adjust_probabilities(base_probs, power_difference):
    """Adjust probabilities based on power difference."""
    attack, balance, defense = base_probs
    
    # Scale factor based on power difference (max shift of 10%)
    adjustment = min(0.1, abs(power_difference) / 15 * 0.1)
    
    if power_difference > 0:  # Home team is stronger
        attack += adjustment
        defense -= adjustment
    else:  # Away team is stronger
        attack -= adjustment
        defense += adjustment
    
    # Ensure probabilities still sum to 1
    balance = 1 - (attack + defense)
    return {'attack': attack, 'balance': balance, 'defense': defense}

def simulate_match(home_team_style, away_team_style, home_team_power, away_team_power):
    power_difference = home_team_power - away_team_power
    
    home_strategy_probs = adjust_probabilities(STYLE_PROBABILITIES[home_team_style], power_difference)
    away_strategy_probs = adjust_probabilities(STYLE_PROBABILITIES[away_team_style], -power_difference)
    
    home_goals, away_goals = 0, 0

    for _ in range(90):
        home_choice = random.choices(list(home_strategy_probs.keys()), weights=home_strategy_probs.values())[0]
        away_choice = random.choices(list(away_strategy_probs.keys()), weights=away_strategy_probs.values())[0]

        goal_probs = PAYOFF_MATRIX.get((home_choice, away_choice), (0.0, 0.0))

        if random.random() < goal_probs[0]:  # Home goal
            home_goals += 1
        if random.random() < goal_probs[1]:  # Away goal
            away_goals += 1
    
    return home_goals, away_goals

def simulate_100_matches(home_team_style, away_team_style, home_power, away_power):
    home_goals_total, away_goals_total = 0, 0
    
    for _ in range(100):
        home_goals, away_goals = simulate_match(home_team_style, away_team_style, home_power, away_power)
        home_goals_total += home_goals
        away_goals_total += away_goals
    
    return home_goals_total / 100, away_goals_total / 100

# Function to load Excel file
def load_excel_file(file_path):
    return pd.read_excel(file_path)

# Function to update the Excel file with predicted scores
def update_excel_with_predictions(df, home_col='Home Team', away_col='Away Team', home_power_col='Home Power', away_power_col='Away Power', predicted_score_col='Predicted Score'):
    # Add a new column for predicted score simulation
    predicted_scores = []

    for index, row in df.iterrows():
        home_team_name = row[home_col]
        away_team_name = row[away_col]
        home_team_power = row[home_power_col]
        away_team_power = row[away_power_col]

        with UnderstatClient() as understat:
            home_team = Team(name=home_team_name, short_title=home_team_name[:3].upper())
            away_team = Team(name=away_team_name, short_title=away_team_name[:3].upper())
            
            # fill stats
            fill_all_stats(home_team, current_season=str(SEASON), last_season=str(SEASON-1), all_seasons=[str(SEASON-1), str(SEASON)], understat=understat)
            fill_all_stats(away_team, current_season=str(SEASON), last_season=str(SEASON-1), all_seasons=[str(SEASON-1), str(SEASON)], understat=understat)

            # Fetch team styles dynamically
            home_team_style = determine_team_play_style(home_team)
            away_team_style = determine_team_play_style(away_team)

        # Simulate the match
        avg_home_goals, avg_away_goals = simulate_100_matches(home_team_style, away_team_style, home_team_power, away_team_power)

        # Append the result as a string "HomeGoals-AwayGoals"
        predicted_scores.append(f"{avg_home_goals:.1f}-{avg_away_goals:.1f}")
        print(predicted_scores)
    # Add the predicted scores to the DataFrame
    df[predicted_score_col] = predicted_scores

    return df

# Example of how to run the update function
file_path = "fixtures_events_with_team_power_and_score.xlsx"
df = load_excel_file(file_path)

# Update the Excel file with predicted scores from simulation
df = update_excel_with_predictions(df)

# Save the updated DataFrame back to Excel
df.to_excel("updated_predictions.xlsx", index=False)

print("Excel file updated with predicted scores!")
