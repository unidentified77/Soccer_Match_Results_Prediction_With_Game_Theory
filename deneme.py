import pandas as pd
import numpy as np
from datetime import date, timedelta
import requests

#######################################################
# 1) Calculate a Single Player’s Power
#######################################################
def calculate_player_power(player_data: dict) -> float:
    """
    Calculates a 'power' rating for a single player using multiple statistics
    fetched from your data sources. This is a more 'complicated' example
    that combines various metrics. Adjust weights/logic as needed.
    
    Example player_data keys we might expect:
      {
         "avg_rating": 7.10,
         "avg_goals": 0.35,
         "avg_xg": 0.45,
         "avg_assists": 0.10,
         "avg_shots": 3.2,
         "avg_key_passes": 2.5,
         "position": "F"
      }
    Returns a single float representing the player's power.
    """
    # Safely extract data with defaults
    avg_rating = player_data.get("avg_rating", 6.0)
    avg_goals = player_data.get("avg_goals", 0.0)
    avg_xg = player_data.get("avg_xg", 0.0)
    avg_assists = player_data.get("avg_assists", 0.0)
    avg_shots = player_data.get("avg_shots", 0.0)
    avg_key_passes = player_data.get("avg_key_passes", 0.0)
    position = player_data.get("position", "").upper()

    # Example weighting approach (tweak as you like):
    base_score = avg_rating * 1.0  # Everyone gets some contribution from average rating

    # More emphasis on goals/xG for forwards:
    if position in ["F", "FW", "ST", "WINGER"]:
        base_score += (avg_goals * 5.0) + (avg_xg * 3.0) + (avg_assists * 1.5)

    # Midfielders might have more emphasis on assists/key_passes:
    elif position in ["M", "MF", "AM", "CM", "DM"]:
        base_score += (avg_goals * 2.0) + (avg_xg * 2.0) + (avg_assists * 3.0) + (avg_key_passes * 1.0)

    # Defenders weigh rating more heavily, fewer goals, maybe tackles or aerial duels:
    elif position in ["D", "DF", "LB", "RB", "CB"]:
        # Example: pretend we had 'avg_tackles' or 'avg_clearances' in data
        avg_tackles = player_data.get("avg_tackles", 0.0)
        avg_clearances = player_data.get("avg_clearances", 0.0)
        base_score += (avg_goals * 1.0) + (avg_tackles * 2.0) + (avg_clearances * 1.5)

    # GKs might weigh clean sheets, saves, etc.
    elif position in ["GK", "GOALKEEPER"]:
        avg_saves = player_data.get("avg_saves", 0.0)
        avg_clean_sheets = player_data.get("avg_clean_sheets", 0.0)
        base_score += (avg_saves * 1.5) + (avg_clean_sheets * 3.0)

    # For any other position not covered, just do a simpler approach
    else:
        base_score += (avg_goals * 2.0) + (avg_xg * 2.0)

    return round(base_score, 3)


#######################################################
# 2) Calculate “Team Synergy” from Team Stats
#######################################################
def calculate_team_synergy(team_stats: dict) -> float:
    """
    Returns a synergy rating (float) for a single team, based on various
    “team-level” metrics you fetch from the API. The idea is that you
    capture how cohesive the team is overall (form, standings, etc.).
    
    Example team_stats keys we might expect:
      {
         "current_rank": 3,
         "points": 42,
         "goal_diff": 15,
         "recent_form": ["W", "W", "D", "W", "L"],  # last 5
         "injured_players": 2,
         "key_suspensions": 1
         ...
      }
    You can get most of these from your existing fetch_* functions
    (fetch_team_form, fetch_team_standing, fetch_injuries, etc.)
    """
    current_rank = team_stats.get("current_rank", 10)  # Lower is better
    goal_diff = team_stats.get("goal_diff", 0)
    recent_form = team_stats.get("recent_form", [])  # array of "W"/"D"/"L"
    injured_players = team_stats.get("injured_players", 0)
    key_suspensions = team_stats.get("key_suspensions", 0)

    # Example form scoring
    form_score = 0.0
    for result in recent_form:
        if result == "W":
            form_score += 1.5
        elif result == "D":
            form_score += 0.7
        # L => 0 points

    # Some quick math to interpret rank:
    # If rank is 1, synergy bonus => 5. If rank is 20, synergy => ~0, etc.
    rank_score = max(0, 6 - 0.2 * (current_rank - 1))

    # Injuries / suspensions might reduce synergy
    penalty = (injured_players + key_suspensions) * 0.7

    # Combine them in a simple formula:
    synergy = form_score + rank_score + (goal_diff * 0.1) - penalty

    # Bound it, for example:
    synergy = max(synergy, 0)  # never go below 0
    synergy = min(synergy, 20) # cap synergy at 20, for instance

    return round(synergy, 3)


#######################################################
# 3) Calculate Formation + Gamestyle Synergy from history_df
#######################################################
def calculate_formation_gamestyle_synergy(home_formation: str,
                                          home_style: str,
                                          away_formation: str,
                                          away_style: str,
                                          history_df: pd.DataFrame) -> (float, float): # type: ignore
    """
    Uses your synergy_from_formation_style logic to look up historical matches
    (from history_df.xlsx) that match the same formations/styles and then adds
    synergy bonuses accordingly.
    
    Returns two floats: synergy_for_home, synergy_for_away
    """
    # Filter rows matching (home_formation + home_style) vs (away_formation + away_style)
    sub = history_df.loc[
        (
            (history_df["Formation_home"] == home_formation)
            & (history_df["style_home"] == home_style)
            & (history_df["Formation_away"] == away_formation)
            & (history_df["style_away"] == away_style)
        )
        |
        (
            (history_df["Formation_home"] == away_formation)
            & (history_df["style_home"] == away_style)
            & (history_df["Formation_away"] == home_formation)
            & (history_df["style_away"] == home_style)
        )
    ]
    # Consider only the last 10 relevant matches
    sub = sub.tail(10)
    if sub.empty:
        return 0.0, 0.0

    synergy_home = 0.0
    synergy_away = 0.0

    for _, row in sub.iterrows():
        hg = row["goals_home"]
        ag = row["goals_away"]
        home_combo = (row["Formation_home"], row["style_home"])
        away_combo = (row["Formation_away"], row["style_away"])

        if hg > ag:  # home team won
            if home_combo == (home_formation, home_style):
                synergy_home += 0.3
            else:
                synergy_away += 0.3
        elif ag > hg:  # away team won
            if away_combo == (home_formation, home_style):
                synergy_home += 0.3
            else:
                synergy_away += 0.3
        # If draw, no synergy increment in this example

    return round(synergy_home, 3), round(synergy_away, 3)


#######################################################
# 4) Find Match and Fixture ID
#######################################################
def find_match_and_fixture_id(home_team_name: str,
                              away_team_name: str,
                              match_date=None,
                              league_id=39,
                              season=2024) -> int:
    """
    Searches API-Football for a fixture that matches the given home/away
    team names (and optionally date), then returns the fixture_id if found.
    
    If match_date is provided (e.g. '2025-04-12'), we limit our search range
    around that date. Otherwise, we can do a broader search.
    
    *You can adapt to do partial or fuzzy matching of the team names if needed.
    *You might also want to match team IDs rather than names.
    
    Returns:
       fixture_id (int) if found, or None if not found.
    """
    BASE_URL = "https://v3.football.api-sports.io"
    API_HEADERS = {
        "x-apisports-key": "078dfd2522b94892b4675b57bd810999",
        "x-apisports-host": "v3.football.api-sports.io"
    }

    if match_date is not None:
        # Narrow the search to +/- 1 day from match_date, for example
        from_date = match_date
        to_date = match_date
    else:
        # Or do some default range, e.g. next 7 days
        today = date.today()
        from_date = today.isoformat()
        to_date = (today + timedelta(days=7)).isoformat()

    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}&from={from_date}&to={to_date}"
    resp = requests.get(url, headers=API_HEADERS)
    data = resp.json()
    
    if not data.get("response"):
        return None

    # Try to find a fixture whose home/away match these names
    for item in data["response"]:
        fix = item.get("fixture", {})
        teams = item.get("teams", {})
        h_name = teams.get("home", {}).get("name", "").lower()
        a_name = teams.get("away", {}).get("name", "").lower()
        if (home_team_name.lower() == h_name) and (away_team_name.lower() == a_name):
            return fix.get("id")  # Found the fixture ID

    # If none matched:
    return None