#!/usr/bin/env python3
"""
excel_cache_maker.py

This module fetches match and player data from API‑Football and Understat,
combines them, and caches the results into an Excel file for later analysis.
It fetches lineup data for a given fixture, retrieves Understat stats for each player
(current season, recent form, career), and also fetches injury information from API‑Football.
The combined data for home and away teams are saved to separate sheets, along with a summary sheet
that includes the total power for the first eleven of each team.
"""

import json
import logging
import pandas as pd

# Import our functions from the power calculator module
from match_player_power_calculator import (
    combine_player_understat_data,
    compute_player_power,
    normalize_name
)
from api_sports_fetch_functions import fetch_team_lineups
from understat_fetch_functions import UnderstatClient

# --- BLENDING WEIGHTS & POSITION WEIGHTS (as defined in the power calculator) ---
ALPHA = 0.5   # Weight for Recent Form
BETA  = 0.3   # Weight for Current Season
GAMMA = 0.2   # Weight for Career
RECENT_MULTIPLIER = 1.5

# (Make sure POSITION_WEIGHTS includes extra metrics if available.)
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
        "red": -3.0,
        "tackles": 0.0,
        "duels": 0.0,
        "dribbles": 1.0,
        "interceptions": 0.0
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
        "red": -2.0,
        "tackles": 0.5,
        "duels": 0.3,
        "dribbles": 0.8,
        "interceptions": 0.5
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
        "red": -3.0,
        "tackles": 1.0,
        "duels": 0.5,
        "dribbles": 0.2,
        "interceptions": 1.0
    },
    "G": {
        "saves": 5.0,
        "clean_sheet": 3.0,
        "yellow": -0.5,
        "red": -3.0
    }
}

# --- SET UP LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_and_cache_fixture_data(fixture_id: str, current_season: str, career_seasons: list, output_excel: str):
    # Fetch lineup data using API‑Football.
    lineup_data = fetch_team_lineups(fixture_id)
    if "response" not in lineup_data or len(lineup_data["response"]) < 2:
        logging.error("Incomplete lineup data for fixture id " + fixture_id)
        return

    home_lineup = lineup_data["response"][0]
    away_lineup = lineup_data["response"][1]

    def process_lineup(lineup):
        team_name = lineup.get("team", {}).get("name", "Unknown")
        players_data = []
        for role in ["startXI", "substitutes"]:
            for entry in lineup.get(role, []):
                pinfo = entry.get("player", {})
                player_name = pinfo.get("name", "Unknown")
                position = pinfo.get("pos", "M")
                api_player_id = str(pinfo.get("id", ""))
                try:
                    power, injured = compute_player_power(
                        player_name, team_name, position, current_season, career_seasons, fixture_id, api_player_id
                    )
                except Exception as e:
                    logging.error(f"Error processing {player_name}: {e}")
                    power, injured = 0, False
                data = combine_player_understat_data(player_name, team_name, current_season, career_seasons, api_player_id)
                players_data.append({
                    "Name": player_name,
                    "Position": position,
                    "API_Player_ID": api_player_id,
                    "Role": "Starter" if role=="startXI" else "Substitute",
                    "Power": power,
                    "Injured": injured,
                    "Current_Stats": json.dumps(data.get("current", {})),
                    "Recent_Stats": json.dumps(data.get("recent", {})),
                    "Career_Stats": json.dumps(data.get("career", {}))
                })
        return team_name, players_data

    home_team, home_players = process_lineup(home_lineup)
    away_team, away_players = process_lineup(away_lineup)

    # Compute total power for first eleven (only non-injured starters).
    def compute_first_eleven_power(players):
        first_eleven = [p for p in players if p["Role"]=="Starter" and not p["Injured"]]
        total = sum(p["Power"] for p in first_eleven)
        return total, first_eleven

    home_total, home_first_eleven = compute_first_eleven_power(home_players)
    away_total, away_first_eleven = compute_first_eleven_power(away_players)

    # Create DataFrames.
    df_home = pd.DataFrame(home_players)
    df_away = pd.DataFrame(away_players)
    summary_df = pd.DataFrame({
        "Team": [home_team, away_team],
        "First_Eleven_Total_Power": [home_total, away_total]
    })

    # Write to Excel.
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df_home.to_excel(writer, sheet_name="Home", index=False)
        df_away.to_excel(writer, sheet_name="Away", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    logging.info(f"Data cached to {output_excel}")

if __name__ == "__main__":
    fixture_id = input("Enter fixture id (from API-Sports): ").strip()
    current_season = "2024"
    career_seasons = ["2020", "2021", "2022", "2023", "2024"]
    output_excel = "fixture_data_cache.xlsx"
    fetch_and_cache_fixture_data(fixture_id, current_season, career_seasons, output_excel)