#!/usr/bin/env python3
"""
excel_data_reader.py

This module reads cached match and player data from an Excel file (cache_data.xlsx)
and then calculates advanced player power scores for a fixture using cached Understat data.
It uses the cached sheets:
  • Lineups (from API‑Football)
  • Understat_Current
  • Understat_Recent
  • Understat_Career

The calculation uses three components:
  SC (Current Season Score),
  RC (Recent Form Score, amplified),
  CC (Career Score),
blended by weights ALPHA, BETA, and GAMMA.
It also marks players with injury status if (for the selected match) API‑Football data indicates so.
"""

import json
import pandas as pd
import logging
import unicodedata
import json
from statistics import mean

# Set up logging.
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Blending Weights & Multiplier.
ALPHA = 0.5  # Recent form weight.
BETA  = 0.3  # Current season weight.
GAMMA = 0.2  # Career weight.
RECENT_MULTIPLIER = 1.5  # Amplify recent form score.

# POSITION WEIGHTS.
POSITION_WEIGHTS = {
    "F": {
        "goals": 5.0,
        "xG": 3.0,
        "assists": 2.0,
        "xA": 1.5,
        "shots": 1.0,
        "key_passes": 1.5,
        "npxG": 2.0,
        "xGChain": 1.0,
        "xGBuildup": 0.5,
        "yellow": -1.0,
        "red": -3.0
    },
    "M": {
        "goals": 3.0,
        "xG": 3.0,
        "assists": 3.0,
        "xA": 2.5,
        "shots": 0.8,
        "key_passes": 2.0,
        "npxG": 1.5,
        "xGChain": 1.0,
        "xGBuildup": 1.0,
        "yellow": -0.5,
        "red": -2.0
    },
    "D": {
        "goals": 2.0,
        "xG": 1.0,
        "assists": 1.0,
        "xA": 0.5,
        "shots": 0.5,
        "key_passes": 1.0,
        "npxG": 1.0,
        "xGChain": 0.5,
        "xGBuildup": 0.5,
        "yellow": -1.0,
        "red": -3.0
    },
    "G": {
        "saves": 5.0,
        "clean_sheet": 3.0,
        "yellow": -0.5,
        "red": -3.0
    }
}

def ascii_normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower().strip()

def normalize_name(name: str) -> str:
    return ascii_normalize(name)

def get_position_category(pos_str: str) -> str:
    pos = pos_str.upper()
    if "GK" in pos or pos.startswith("G"):
        return "G"
    elif "D" in pos:
        return "D"
    elif "F" in pos:
        return "F"
    else:
        return "M"

def compute_component_score_full(stats: dict, weights: dict) -> float:
    score = 0.0
    for metric, weight in weights.items():
        try:
            value = float(stats.get(metric, 0))
        except (TypeError, ValueError):
            value = 0.0
        score += value * weight
    return score

def compute_gk_power(stats: dict, weights: dict) -> float:
    try:
        saves = float(stats.get("saves", 0))
    except:
        saves = 0.0
    try:
        cs = float(stats.get("clean_sheet", 0))
    except:
        cs = 0.0
    return saves * weights.get("saves", 0) + cs * weights.get("clean_sheet", 0)

def load_cached_data(filename="cache_data.xlsx"):
    xl = pd.ExcelFile(filename)
    df_lineups = xl.parse("Lineups")
    df_current = xl.parse("Understat_Current")
    df_recent = xl.parse("Understat_Recent")
    df_career = xl.parse("Understat_Career")
    return df_lineups, df_current, df_recent, df_career

def get_understat_data(df, player_name: str, team: str) -> dict:
    for _, row in df.iterrows():
        if normalize_name(row["player_name"]) == normalize_name(player_name) and normalize_name(row["team"]) == normalize_name(team):
            try:
                return json.loads(row["data"])
            except Exception as e:
                logging.error(f"Error loading JSON for {player_name}: {e}")
                return {}
    return {}

def compute_player_power(player_name: str, team: str, position: str, current_season: str, career_seasons: list) -> float:
    pos_cat = get_position_category(position)
    if pos_cat == "G":
        weights = POSITION_WEIGHTS["G"]
    else:
        weights = POSITION_WEIGHTS.get(pos_cat, POSITION_WEIGHTS["M"])
    
    df_lineups, df_current, df_recent, df_career = load_cached_data()
    
    current = get_understat_data(df_current, player_name, team)
    recent = get_understat_data(df_recent, player_name, team)
    career = get_understat_data(df_career, player_name, team)
    
    if pos_cat == "G":
        sc = compute_gk_power(current, weights)
        cc = compute_gk_power(career, weights)
        rc = RECENT_MULTIPLIER * compute_gk_power(recent, weights)
    else:
        sc = compute_component_score_full(current, weights)
        cc = compute_component_score_full(career, weights)
        rc = RECENT_MULTIPLIER * compute_component_score_full(recent, weights)
    
    # For debugging, print out the JSON for recent and career stats.
    print(f"\nData for {player_name} ({position}):")
    print("  Normalized Recent stats JSON:")
    print(json.dumps(recent, indent=2))
    print("  Normalized Career stats JSON:")
    print(json.dumps(career, indent=2))
    
    final_score = ALPHA * rc + BETA * sc + GAMMA * cc
    return final_score

def calculate_match_player_powers(current_season: str, career_seasons: list) -> dict:
    df_lineups, _, _, _ = load_cached_data()
    
    teams_power = {}
    for _, row in df_lineups.iterrows():
        team = row["team"]
        player_name = row["player_name"]
        position = row["position"]
        api_player_id = row["api_player_id"]
        order = row.get("order", 99)
        # Determine status based on order; if order < 11: First Eleven, else Subs.
        status = "First Eleven" if order < 11 else "Subs"
        # (In your project, you may update the "injured" field based on API‑Football injury data.)
        injured = row.get("injured", False)
        if injured:
            status = "Injured"
        power = compute_player_power(player_name, team, position, current_season, career_seasons)
        teams_power.setdefault(team, {})[player_name] = {"position": position, "power": power, "status": status}
    return teams_power

if __name__ == "__main__":
    current_season = "2024"
    career_seasons = ["2020", "2021", "2022", "2023", "2024"]
    
    teams_power = calculate_match_player_powers(current_season, career_seasons)
    
    print("\nPlayer Power Scores for the Match (from cached Excel data):")
    for team, players in teams_power.items():
        print(f"\n--- TEAM: {team} ---")
        for pname, info in players.items():
            print(f"{pname:<25} (Pos: {info['position']}) -> Power: {info['power']:.2f}  Status: {info['status']}")