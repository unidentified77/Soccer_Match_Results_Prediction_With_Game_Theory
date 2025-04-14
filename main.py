#!/usr/bin/env python3
import requests
import logging
import pandas as pd
import json
from datetime import datetime, timedelta

# --------------------------------------------------------
# CONFIG & HELPERS
# --------------------------------------------------------
API_KEY = "078dfd2522b94892b4675b57bd810999"
API_HOST = "v3.football.api-sports.io"
BASE_URL = f"https://{API_HOST}"
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print("[DEBUG]", msg)

# --------------------------------------------------------
# 1) FETCHING DATA FROM API-FOOTBALL
# --------------------------------------------------------

def fetch_fixture_details(fixture_id: int) -> dict:
    """
    Fetch single fixture details from /fixtures?id={fixture_id}.
    Includes date/time, venue, scoreboard, events, etc.
    """
    url = f"{BASE_URL}/fixtures?id={fixture_id}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    # Typically data["response"] is a list with 1 item if fixture_id is valid
    if not data.get("response"):
        return {}
    return data["response"][0]

def fetch_lineups(fixture_id: int) -> list:
    """
    /fixtures/lineups?fixture=...
    Returns list of lineups for home & away teams.
    """
    url = f"{BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    return data.get("response", [])

def fetch_injuries(fixture_id: int, team_id: int, season=2024) -> list:
    """
    /injuries?fixture={fixture_id}&team={team_id}&season=...
    Returns list of injured players for that fixture & team.
    """
    url = f"{BASE_URL}/injuries?fixture={fixture_id}&team={team_id}&season={season}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    out = []
    for item in data.get("response", []):
        pl_name = item.get("player", {}).get("name")
        if pl_name:
            out.append(pl_name)
    return out

def fetch_team_form(team_id: int, season=2024, last_n=5) -> list:
    """
    /fixtures?team=..&season=..&last=5
    Return W/D/L for the last 5 completed matches (from the perspective of team_id).
    """
    url = f"{BASE_URL}/fixtures?team={team_id}&season={season}&last={last_n}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    form_list = []
    for fx in data.get("response", []):
        goals_home = fx["goals"]["home"]
        goals_away = fx["goals"]["away"]
        home_id = fx["teams"]["home"]["id"]
        away_id = fx["teams"]["away"]["id"]
        if goals_home is None or goals_away is None:
            continue  # not finished
        if home_id == team_id:
            # Our team is home => compare goals
            if goals_home > goals_away:
                form_list.append("W")
            elif goals_home < goals_away:
                form_list.append("L")
            else:
                form_list.append("D")
        else:
            # Our team is away
            if goals_away > goals_home:
                form_list.append("W")
            elif goals_away < goals_home:
                form_list.append("L")
            else:
                form_list.append("D")
    return form_list

def fetch_headtohead(team1_id: int, team2_id: int, last_n=5) -> list:
    """
    /fixtures/headtohead?h2h={team1_id}-{team2_id}
    Return up to last N match results between the two teams.
    """
    url = f"{BASE_URL}/fixtures/headtohead?h2h={team1_id}-{team2_id}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    if not data.get("response"):
        return []
    # Sort by date desc, then slice last_n
    h2h_list = sorted(data["response"], key=lambda x: x["fixture"]["timestamp"], reverse=True)
    return h2h_list[:last_n]

def fetch_standings(league_id=39, season=2024) -> list:
    """
    /standings?league=39&season=2024
    Returns entire league table. We'll parse for a specific team’s rank, points, etc.
    """
    url = f"{BASE_URL}/standings?league={league_id}&season={season}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    if not data.get("response"):
        return []
    # Usually data["response"][0]["league"]["standings"] is a list of lists
    return data["response"][0]["league"]["standings"][0]

def fetch_team_statistics(team_id: int, league_id=39, season=2024) -> dict:
    """
    /teams/statistics?team=...&league=...&season=...
    This returns dict with form, fixtures, goals (for/against), etc.
    """
    url = f"{BASE_URL}/teams/statistics?team={team_id}&league={league_id}&season={season}"
    headers = {"x-apisports-key": API_KEY, "x-apisports-host": API_HOST}
    r = requests.get(url, headers=headers)
    data = r.json()
    # "response" is typically a single dict
    return data.get("response", {})

# --------------------------------------------------------
# 2) PARSING / CALCULATING TEAM & PLAYER POWER
# --------------------------------------------------------

def calculate_player_power(player_data: dict) -> float:
    """
    Example of a 'complicated' rating system for one player:
      - player_data might have "avg_rating", "avg_goals", "avg_xg", "avg_assists"...
      - position = "F", "M", "D", "GK", etc.
    We'll just do a sample weighting approach here. You can expand it.
    """
    position = player_data.get("position", "F").upper()
    avg_rating = player_data.get("avg_rating", 6.5)
    avg_goals = player_data.get("avg_goals", 0.2)
    avg_xg = player_data.get("avg_xg", 0.3)
    avg_assists = player_data.get("avg_assists", 0.1)

    # Everyone gets some contribution from rating
    power = avg_rating

    # Then add position-based weighting
    if position in ["F", "FW", "ST", "WINGER"]:
        power += (avg_goals * 5) + (avg_xg * 3) + (avg_assists * 2)
    elif position in ["M", "MF", "AM", "CM"]:
        power += (avg_goals * 2) + (avg_xg * 2) + (avg_assists * 3)
    elif position in ["D", "DF", "CB", "LB", "RB"]:
        # Suppose we have 'avg_tackles' or 'avg_clearances' in data
        avg_tackles = player_data.get("avg_tackles", 1.0)
        avg_clear = player_data.get("avg_clearances", 2.0)
        power += (avg_goals * 1) + (avg_tackles * 2) + (avg_clear * 1.5)
    elif position in ["GK"]:
        avg_saves = player_data.get("avg_saves", 3.0)
        avg_clean_sheets = player_data.get("avg_clean_sheets", 0.2)
        power += (avg_saves * 1.5) + (avg_clean_sheets * 3)

    return round(power, 2)

def calculate_team_synergy(team_stats: dict) -> float:
    """
    Overall synergy from team-level metrics:
      - rank => better rank => more synergy
      - goal_diff => bigger => better synergy
      - injuries => each reduces synergy
      - recent_form => W=1.5, D=0.7, L=0
    """
    rank_ = team_stats.get("rank", 10)
    goal_diff = team_stats.get("goal_diff", 0)
    injuries = team_stats.get("injuries_count", 0)
    form_arr = team_stats.get("recent_form", [])

    # form
    form_score = 0
    for f in form_arr:
        if f == "W":
            form_score += 1.5
        elif f == "D":
            form_score += 0.7

    # rank-based
    rank_score = max(0, 6 - 0.2 * (rank_ - 1))  # e.g. rank=1 => +5.8 synergy, rank=20 => ~2 synergy

    # injuries => each -0.5 synergy
    penalty = injuries * 0.5

    synergy = form_score + rank_score + (goal_diff * 0.1) - penalty
    # Bound it
    if synergy < 0:
        synergy = 0
    return round(synergy, 2)

def calculate_formation_and_style_synergy(home_form, home_style, away_form, away_style, history_df: pd.DataFrame) -> (float, float):
    """
    Uses your synergy_from_formation_style logic with a history_df that has columns:
      ["Formation_home","style_home","Formation_away","style_away","goals_home","goals_away",...]
    We'll pick the last 10 rows that match this combination in either orientation, 
    then increment synergy +0.3 each time that combo 'wins'.
    """
    sub = history_df.loc[
        (
            (history_df["Formation_home"] == home_form) &
            (history_df["style_home"] == home_style) &
            (history_df["Formation_away"] == away_form) &
            (history_df["style_away"] == away_style)
        )
        |
        (
            (history_df["Formation_home"] == away_form) &
            (history_df["style_home"] == away_style) &
            (history_df["Formation_away"] == home_form) &
            (history_df["style_away"] == home_style)
        )
    ]
    sub = sub.tail(10)  # last 10
    if sub.empty:
        return (0.0, 0.0)

    home_bonus = 0.0
    away_bonus = 0.0
    for _, row in sub.iterrows():
        hg = row["goals_home"]
        ag = row["goals_away"]
        # if home side is the one with (home_form,home_style) => increment if it wins
        if hg > ag:
            if (row["Formation_home"] == home_form) and (row["style_home"] == home_style):
                home_bonus += 0.3
            else:
                away_bonus += 0.3
        elif ag > hg:
            if (row["Formation_away"] == home_form) and (row["style_away"] == home_style):
                home_bonus += 0.3
            else:
                away_bonus += 0.3
    return (round(home_bonus,2), round(away_bonus,2))

# --------------------------------------------------------
# 3) MAIN WORKFLOW
# --------------------------------------------------------

def main():
    # 0) Setup logging / debugging
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

    # 1) Choose a fixture_id to analyze:
    fixture_id = 1208332  # Example: West Ham (48) vs Bournemouth (35)

    # 2) Fetch the fixture details
    fixture_data = fetch_fixture_details(fixture_id)
    if not fixture_data:
        print(f"No data found for fixture_id={fixture_id}")
        return

    # Parse relevant info
    home_team_id = fixture_data["teams"]["home"]["id"]
    away_team_id = fixture_data["teams"]["away"]["id"]
    home_team_name = fixture_data["teams"]["home"]["name"]
    away_team_name = fixture_data["teams"]["away"]["name"]
    league_id = fixture_data["league"]["id"]  # 39 typically

    # 3) We can fetch lineups (though here, formation is null).
    lineups = fetch_lineups(fixture_id)
    # We'll store a fallback formation or style if they're null
    home_formation = "Unknown Formation"
    away_formation = "Unknown Formation"

    # Example: if lineups are not empty, check the .get("formation") for each:
    for ln in lineups:
        if ln["team"]["id"] == home_team_id:
            if ln["formation"]:
                home_formation = ln["formation"]
        else:
            if ln["formation"]:
                away_formation = ln["formation"]

    # 4) We can pick a style for each side (dummy logic or from stats).
    #    Since we don't have direct style data from API-Football, we'll guess:
    home_style = "Possession Based" if home_formation=="4-3-3" else "Balanced"
    away_style = "Counter Attack" if away_formation=="4-4-2" else "Balanced"

    # 5) Injuries for each team:
    home_injuries = fetch_injuries(fixture_id, home_team_id, season=2024)
    away_injuries = fetch_injuries(fixture_id, away_team_id, season=2024)

    # 6) Team form (W, D, L)
    home_form_arr = fetch_team_form(home_team_id, season=2024, last_n=5)
    away_form_arr = fetch_team_form(away_team_id, season=2024, last_n=5)

    # 7) Standings => parse for rank, points, etc.
    standings_data = fetch_standings(league_id=league_id, season=2024)
    # We'll find each team's entry
    def get_team_standing(team_id, stand_table):
        for row in stand_table:
            if row["team"]["id"] == team_id:
                return row
        return None

    home_stand = get_team_standing(home_team_id, standings_data)
    away_stand = get_team_standing(away_team_id, standings_data)

    # 8) Team statistics => form, goals, etc.
    home_stats = fetch_team_statistics(home_team_id, league_id, season=2024)
    away_stats = fetch_team_statistics(away_team_id, league_id, season=2024)

    # We'll assemble a dict for synergy calculation:
    home_synergy_dict = {
        "rank": home_stand["rank"] if home_stand else 10,
        "goal_diff": home_stand["goalsDiff"] if home_stand else 0,
        "injuries_count": len(home_injuries),
        "recent_form": home_form_arr,  # e.g. ["W","L","D",...]
    }
    away_synergy_dict = {
        "rank": away_stand["rank"] if away_stand else 10,
        "goal_diff": away_stand["goalsDiff"] if away_stand else 0,
        "injuries_count": len(away_injuries),
        "recent_form": away_form_arr,
    }

    # 9) Calculate “team synergy”
    home_team_synergy = calculate_team_synergy(home_synergy_dict)
    away_team_synergy = calculate_team_synergy(away_synergy_dict)

    # 10) Formation + style synergy from your history_df.xlsx
    #     We'll load that local XLSX:
    #     (Note: you already have it in your code, synergycheck.py)
    try:
        history_df = pd.read_excel("history_df.xlsx")
    except:
        history_df = pd.DataFrame()
    (form_style_synergy_home, form_style_synergy_away) = (0.0, 0.0)
    if not history_df.empty:
        form_style_synergy_home, form_style_synergy_away = \
            calculate_formation_and_style_synergy(home_formation, home_style,
                                                  away_formation, away_style,
                                                  history_df)

    # 11) Summation of “Team synergy” + “Formation+Style synergy” = synergy_total
    home_total_synergy = home_team_synergy + form_style_synergy_home
    away_total_synergy = away_team_synergy + form_style_synergy_away

    # 12) Now we do “player power.” Typically you’d have an Understat or other
    #     data source for each player. We’ll do a quick dummy approach:
    #     (In your real code, you’d fetch from Understat or your own DB.)
    #     We'll pretend each team has 3 players with sample stats:
    home_players_data = [
        {"player_name": "PlayerA", "position": "F", "avg_rating": 7.0, "avg_goals": 0.3, "avg_xg": 0.4},
        {"player_name": "PlayerB", "position": "M", "avg_rating": 6.5, "avg_goals": 0.1, "avg_xg": 0.2, "avg_assists": 0.2},
        {"player_name": "PlayerC", "position": "D", "avg_rating": 7.2, "avg_goals": 0.05, "avg_tackles": 3.0}
    ]
    away_players_data = [
        {"player_name": "PlayerX", "position": "F", "avg_rating": 7.1, "avg_goals": 0.35, "avg_xg": 0.5},
        {"player_name": "PlayerY", "position": "GK", "avg_rating": 6.8, "avg_saves": 4.0, "avg_clean_sheets": 0.1},
        {"player_name": "PlayerZ", "position": "M", "avg_rating": 7.0, "avg_goals": 0.2, "avg_assists": 0.3}
    ]

    home_player_powers = [calculate_player_power(p) for p in home_players_data]
    away_player_powers = [calculate_player_power(p) for p in away_players_data]
    home_player_sum = sum(home_player_powers)
    away_player_sum = sum(away_player_powers)

    # 13) Final team power = sum_of_player_powers + synergy_total
    home_final_power = home_player_sum + home_total_synergy
    away_final_power = away_player_sum + away_total_synergy

    # 14) Print everything for clarity
    print("============================================================")
    print(f"Fixture {fixture_id}: {home_team_name} vs {away_team_name}")
    print("Home Formation/Style:", home_formation, "/", home_style)
    print("Away Formation/Style:", away_formation, "/", away_style)
    print("Home injuries:", home_injuries)
    print("Away injuries:", away_injuries)
    print("Home synergy data:", home_synergy_dict)
    print("Away synergy data:", away_synergy_dict)
    print(f"Home synergy => {home_team_synergy} + (F+S synergy {form_style_synergy_home}) => {home_total_synergy}")
    print(f"Away synergy => {away_team_synergy} + (F+S synergy {form_style_synergy_away}) => {away_total_synergy}")
    print("Home players & powers:", list(zip([p["player_name"] for p in home_players_data], home_player_powers)))
    print("Away players & powers:", list(zip([p["player_name"] for p in away_players_data], away_player_powers)))
    print("Home sum of player power:", home_player_sum)
    print("Away sum of player power:", away_player_sum)
    print("============================================================")
    print(f"Home FINAL POWER = {home_final_power:.2f}")
    print(f"Away FINAL POWER = {away_final_power:.2f}")
    print("============================================================")


if __name__ == "__main__":
    main()