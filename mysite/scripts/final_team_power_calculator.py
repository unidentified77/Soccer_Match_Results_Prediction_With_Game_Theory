#!/usr/bin/env python3
"""
final_team_power_calculator.py

This script calculates the final team power for a selected fixture.
It uses three components:
  1) First Eleven Power – the sum of the power scores of the starting eleven players,
  2) Synergy Bonus – based on the formation & game style matchup using historical data,
  3) Overall Team Strength – derived from team statistics.

Final Team Power = First Eleven Power + Synergy Bonus + Overall Team Strength

Results are printed and saved to an Excel file.
"""

import json
import logging
import pandas as pd
import requests
from datetime import datetime
from statistics import mean

# Import functions from our other modules
from match_player_power_calculator import (
    calculate_match_player_powers, save_results_to_excel
)
from synergycheck import synergy_from_formation_style
from team_power import Team, fill_all_stats
from utils import UnderstatClient

# Configuration
BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",  # Replace with your API key
    "x-apisports-host": "v3.football.api-sports.io"
}
LEAGUE_ID = 39
SEASON = "2024"  # Current season (as string)
LAST_SEASON = str(int(SEASON) - 1)
CAREER_SEASONS = [LAST_SEASON, SEASON]  # Adjust if you want more seasons

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------------------------------------------------------
# Helper functions for team-level calculations
# ------------------------------------------------------------------
def get_total_first_eleven_power(player_powers: dict) -> dict:
    """Return a dict with total first eleven power per team."""
    totals = {}
    for side in player_powers:
        totals[side] = sum(p["power"] for p in player_powers[side]["first_eleven"])
    return totals

def get_synergy_bonus(home_formation: str, home_style: str,
                      away_formation: str, away_style: str,
                      history_filename: str = "history_df.xlsx") -> tuple[float, float]:
    """
    Read historical data from Excel and calculate synergy bonus.
    Returns a tuple: (home_bonus, away_bonus)
    """
    try:
        history_df = pd.read_excel(history_filename)
    except Exception as e:
        logging.warning(f"Error loading history data: {e}")
        return (0.0, 0.0)
    return synergy_from_formation_style(home_formation, home_style, away_formation, away_style, history_df)

def get_team_overall_strength(team: Team) -> float:
    """
    Calculate overall team strength from team statistics.
    The team’s calculate_team_strength() method is used.
    """
    return team.calculate_team_strength()

# ------------------------------------------------------------------
# Main function to calculate final team powers
# ------------------------------------------------------------------
def calculate_final_team_powers(fixture_id: str) -> dict:
    # 1. Get individual player powers (using our existing match_player_power_calculator module)
    logging.info("Calculating individual player powers...")
    player_powers = calculate_match_player_powers(fixture_id, SEASON, CAREER_SEASONS)
    if not player_powers:
        logging.error("Player power calculation failed!")
        return {}
    first_eleven_totals = get_total_first_eleven_power(player_powers)
    
    # 2. Create team objects and fill overall team stats via Understat
    logging.info("Filling team overall statistics...")
    with UnderstatClient() as understat:
        # Get team names from the lineup endpoint (API‑Football)
        lineup_url = f"{BASE_URL}/fixtures/lineups?fixture={fixture_id}"
        lineup_data = requests.get(lineup_url, headers=API_HEADERS).json()
        if "response" not in lineup_data or len(lineup_data["response"]) < 2:
            logging.error("Incomplete lineup data for fixture!")
            return {}
        home_team_name = lineup_data["response"][0]["team"]["name"]
        away_team_name = lineup_data["response"][1]["team"]["name"]
    
        home_team = Team(name=home_team_name, short_title=home_team_name[:3].upper())
        away_team = Team(name=away_team_name, short_title=away_team_name[:3].upper())
    
        # Fill team stats for current and last season
        all_seasons = [LAST_SEASON, SEASON]
        fill_all_stats(home_team, current_season=SEASON, last_season=LAST_SEASON, all_seasons=all_seasons, understat=understat)
        fill_all_stats(away_team, current_season=SEASON, last_season=LAST_SEASON, all_seasons=all_seasons, understat=understat)
    
        # For formation and style, use team attributes (if available) or set defaults
        home_formation = home_team.last_match_formation if home_team.last_match_formation else "4-3-3"
        away_formation = away_team.last_match_formation if away_team.last_match_formation else "4-4-2"
        home_style = home_team.style if home_team.style else "Attacking"
        away_style = away_team.style if away_team.style else "Defensive"
    
        home_overall = get_team_overall_strength(home_team)
        away_overall = get_team_overall_strength(away_team)
    
    # 3. Get synergy bonus from formation & style history
    logging.info("Calculating synergy bonus...")
    synergy_home, synergy_away = get_synergy_bonus(home_formation, home_style, away_formation, away_style)
    
    # 4. Final team power = First Eleven Power + Synergy Bonus + Overall Team Strength
    final_home_power = first_eleven_totals.get("home", 0.0) + synergy_home + home_overall
    final_away_power = first_eleven_totals.get("away", 0.0) + synergy_away + away_overall
    
    results = {
        "fixture_id": fixture_id,
        "home_team": home_team.name,
        "away_team": away_team.name,
        "final_home_power": final_home_power,
        "final_away_power": final_away_power,
        "first_eleven_totals": first_eleven_totals,
        "synergy_bonus": {"home": synergy_home, "away": synergy_away},
        "overall_strength": {"home": home_overall, "away": away_overall}
    }
    return results

def main():
    fixture_id = input("Enter fixture id (from API-Sports): ").strip()
    results = calculate_final_team_powers(fixture_id)
    if results:
        print("\nFinal Team Powers:")
        print(f"Fixture ID: {results['fixture_id']}")
        print(f"{results['home_team']} Final Power: {results['final_home_power']:.2f}")
        print(f"{results['away_team']} Final Power: {results['final_away_power']:.2f}")
        # Save final results to Excel
        df = pd.DataFrame([results])
        output_filename = "final_team_powers.xlsx"
        df.to_excel(output_filename, index=False)
        print(f"Final team power results saved to {output_filename}")
    else:
        print("Final team power calculation failed.")

if __name__ == "__main__":
    main()