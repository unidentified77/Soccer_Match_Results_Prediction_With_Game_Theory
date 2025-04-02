import requests
import pandas as pd
from datetime import date, timedelta

# API Configuration
BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": "078dfd2522b94892b4675b57bd810999"
}
LEAGUE_ID = 39  # Example: Premier League

# Function to fetch fixtures
def fetch_fixtures(league_id, limit=25):
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

# Main function
def main():
    fixtures = fetch_fixtures(LEAGUE_ID, limit=25)  # Fetch fixtures
    
    rows = []
    for fixture in fixtures:
        home_team = fixture["home_team"]
        away_team = fixture["away_team"]
        events, score = fetch_events_and_score(fixture["fixture_id"], home_team, away_team)  # Fetch events and score for the fixture
        row = {
            "ID": fixture["fixture_id"],
            "Home Team": home_team,
            "Away Team": away_team,
            "Score": score,  # Add score column dynamically
            **events  # Merge event data into the row
        }
        rows.append(row)
    
    # Create a DataFrame and save it to an Excel file
    df = pd.DataFrame(rows)
    df.to_excel("fixtures_events_with_dynamic_score.xlsx", index=False)
    print("Excel file with events and dynamic scores saved!")

# Run the main function
if __name__ == "__main__":
    main()
