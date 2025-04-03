import requests
import pandas as pd
from datetime import date, timedelta
from predictor import Team, fill_all_stats, adjust_team_power_with_bonus, poisson_pmf, predict_score_poisson
from utils import UnderstatClient
from team_power import Team, fill_all_stats
from tactics import determine_team_formation, determine_team_play_style
from gametheory import synergy_from_formation_style, calculate_combination_percentages

# API Configuration
BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": "078dfd2522b94892b4675b57bd810999"
}
LEAGUE_ID = 39  # Example: Premier League

def load_history(filename="history_df.xlsx"):
    try:
        return pd.read_excel(filename)
    except Exception as e:
        print(f"Error loading history data: {e}")
        return pd.DataFrame()

# Function to fetch fixtures
def fetch_fixtures(league_id, limit=3):  # Limit to 3 fixtures for testing
    fixtures = []
    url = f"{BASE_URL}/fixtures?league={league_id}&last={limit}"
    response = requests.get(url, headers=API_HEADERS).json()
    for item in response.get("response", []):
        fixtures.append({
            "fixture_id": item["fixture"]["id"],
            "date": item["fixture"]["date"],
            "home_team": item["teams"]["home"]["name"],
            "away_team": item["teams"]["away"]["name"]
        })
    return fixtures

# Function to fetch events and calculate the score dynamically
def fetch_events_and_score(fixture_id, home_team, away_team):
    url = f"{BASE_URL}/fixtures/events?fixture={fixture_id}"
    response = requests.get(url, headers=API_HEADERS).json()
    event_data = {interval: [] for interval in range(0, 95, 5)}  # Include 90-minute interval
    
    home_goals = 0
    away_goals = 0
    
    # List to hold all events
    for event in response.get("response", []):
        minute = event.get("time", {}).get("elapsed", 0)
        event_type = event.get("type", "")
        detail = event.get("detail", "")
        team = event.get("team", {}).get("name", "")
        
        # Update score for goal events
        if event_type == "Goal":
            if team == home_team:
                home_goals += 1
            elif team == away_team:
                away_goals += 1
        
        # Categorize events into 5-minute intervals
        interval = min((minute // 5) * 5, 90)  # Ensure no interval exceeds 90
        event_data[interval].append(f"{team}: {event_type} ({detail})")
    
    # Calculate final score based on goals
    score = f"{home_goals} - {away_goals}"
    
    # Return event data and score
    return {k: " | ".join(v) for k, v in event_data.items()}, score

# Function to calculate team powers and predicted score
def calculate_team_powers_and_predicted_score(home_team_name, away_team_name, fixture_id, history_df):
    # Create Team objects
    home_team = Team(name=home_team_name, short_title=home_team_name[:3].upper())
    away_team = Team(name=away_team_name, short_title=away_team_name[:3].upper())

    # Initialize UnderstatClient and fetch team stats
    with UnderstatClient() as understat:
        fill_all_stats(home_team, current_season="2024", last_season="2023", all_seasons=["2023", "2024"], understat=understat)
        fill_all_stats(away_team, current_season="2024", last_season="2023", all_seasons=["2023", "2024"], understat=understat)
    
    # Calculate team strength (base strength + synergy)
    home_team.base_strength = home_team.calculate_team_strength()
    away_team.base_strength = away_team.calculate_team_strength()

    formA = home_team.last_match_formation or home_team.formation
    styA = home_team.style
    formB = away_team.last_match_formation or away_team.formation
    styB = away_team.style

    # Adjust team power with synergy
    bonusA, bonusB = synergy_from_formation_style(formA, styA, formB, styB, history_df)
    home_strength_adj = adjust_team_power_with_bonus(home_team, bonusA)
    away_strength_adj = adjust_team_power_with_bonus(away_team, bonusB)

    # Apply home advantage
    home_strength_adj += 1.0

    # Calculate final strengths
    home_team.final_strength = max(home_strength_adj, 0.0)
    away_team.final_strength = max(away_strength_adj, 0.0)

    # Calculate Poisson distribution parameters
    lam_home = 0.25 * home_team.final_strength
    lam_away = 0.25 * away_team.final_strength

    # Predict the score
    phg, pag = predict_score_poisson(lam_home, lam_away, max_goals=6)

    return home_strength_adj, away_strength_adj, f"{phg}-{pag}"

# Main function
def main():
    fixtures = fetch_fixtures(LEAGUE_ID, limit=50)  # Limit to 3 fixtures for testing
    
    # Load history data
    history_df = load_history("history_df.xlsx")

    rows = []
    for fixture in fixtures:
        home_team = fixture["home_team"]
        away_team = fixture["away_team"]
        fixture_id = fixture["fixture_id"]
        
        # Debug print
        print(f"Fetching events and score for FixtureID={fixture_id} - {home_team} vs {away_team}")
        
        # Fetch events and score for the fixture
        events, score = fetch_events_and_score(fixture_id, home_team, away_team)
        
        # Debug print
        print(f"Events and score fetched for FixtureID={fixture_id}")
        
        # Calculate team powers and predicted score
        home_power, away_power, predicted_score = calculate_team_powers_and_predicted_score(home_team, away_team, fixture_id, history_df)
        
        # Debug print
        print(f"Team powers and predicted score calculated for FixtureID={fixture_id}")
        
        # Create a row with event data, score, team powers, and predicted score
        row = {
            "ID": fixture_id,
            "Home Team": home_team,
            "Away Team": away_team,
            "Score": score,  # Add score column dynamically
            "Home Power": home_power,
            "Away Power": away_power,
            "Predicted Score": predicted_score,
            **events  # Merge event data into the row
        }
        rows.append(row)
    
    # Create a DataFrame and save it to an Excel file
    df = pd.DataFrame(rows)
    df.to_excel("fixtures_events_with_team_power_and_score.xlsx", index=False)
    print("Excel file with events, team powers, and predicted scores saved!")

# Run the main function
if __name__ == "__main__":
    main()
