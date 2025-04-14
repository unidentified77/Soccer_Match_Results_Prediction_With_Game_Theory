#!/usr/bin/env python3
"""
match_analysis.py

This is the main routine for match analysis.
It performs the following:
  1. Fetches upcoming fixtures using API‑Football.
  2. Lets the user select a fixture.
  3. Creates Team objects and fills them with Understat data (using understat_data functions),
     and real FBref stats (via api_football functions).
  4. Determines each team’s formation and play style.
  5. Calculates a synergy bonus from formation and style.
  6. Selects the first eleven players and sums their power.
  7. Computes the final team power = first eleven sum + synergy bonus.
  8. Prints all aggregated data and final results.
"""

import logging
import pandas as pd
from datetime import date, timedelta
from understatapi import UnderstatClient
from api_football import fetch_fixtures_in_range, get_possession_percentage, get_passing_accuracy, get_shots_on_target, get_total_shots
from team import Team
from understat_data import fill_all_stats
from tactics import determine_team_formation, determine_team_play_style
from synergy import synergy_from_formation_style
from team_utils import pick_first_eleven

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    upcoming = fetch_fixtures_in_range()
    if not upcoming:
        print("No fixtures found.")
        return

    print("\nFixtures in EXACT 7 days:\n")
    for i, fix in enumerate(upcoming):
        dt_str = fix["date"].replace("T", " ")[:16]
        print(f"[{i}] FixtureID={fix['fixture_id']}  {dt_str}  {fix['home_team_name']} vs {fix['away_team_name']}")

    try:
        idx = int(input("\nSelect a fixture index to analyze: "))
        if idx < 0 or idx >= len(upcoming):
            raise IndexError
    except Exception:
        print("Invalid choice. Exiting.")
        return

    selected = upcoming[idx]
    fixture_id = selected["fixture_id"]
    fixture_date = selected["date"]
    home_team_name = selected["home_team_name"]
    away_team_name = selected["away_team_name"]

    print(f"\nSelected Fixture: {fixture_id}: {home_team_name} vs {away_team_name} on {fixture_date}\n")

    # Create Team objects.
    home_team = Team(name=home_team_name, short_title=home_team_name[:3].upper())
    away_team = Team(name=away_team_name, short_title=away_team_name[:3].upper())

    # Define seasons.
    current_season = "2024"
    last_season = "2023"
    all_seasons = ["2023", "2024"]

    # Load synergy history if available.
    try:
        history_df = pd.read_excel("history_df.xlsx")
    except Exception as e:
        logging.warning(f"Could not load synergy history: {e}")
        history_df = pd.DataFrame()

    # Fill team stats using Understat data.
    with UnderstatClient() as understat:
        for s in all_seasons:
            home_team.matches.extend(home_team.get_match_data(s, understat))
            away_team.matches.extend(away_team.get_match_data(s, understat))
        fill_all_stats(home_team, current_season, last_season, all_seasons, understat)
        fill_all_stats(away_team, current_season, last_season, all_seasons, understat)

    # Fetch real FBref stats.
    home_team.possession_percentage = get_possession_percentage(home_team.name, current_season)
    home_team.passing_accuracy = get_passing_accuracy(home_team.name, current_season)
    home_team.shots_on_target = get_shots_on_target(home_team.name, current_season)
    home_team.total_shots = get_total_shots(home_team.name, current_season)
    away_team.possession_percentage = get_possession_percentage(away_team.name, current_season)
    away_team.passing_accuracy = get_passing_accuracy(away_team.name, current_season)
    away_team.shots_on_target = get_shots_on_target(away_team.name, current_season)
    away_team.total_shots = get_total_shots(away_team.name, current_season)

    # Determine formation and style.
    home_team.formation = determine_team_formation(home_team)
    away_team.formation = determine_team_formation(away_team)
    home_team.style = determine_team_play_style(home_team)
    away_team.style = determine_team_play_style(away_team)

    # Calculate synergy bonus.
    synergy_home, synergy_away = synergy_from_formation_style(home_team.formation, home_team.style, away_team.formation, away_team.style, history_df)
    home_team.synergy_power = synergy_home
    away_team.synergy_power = synergy_away

    # Debug output.
    print("\n--- Aggregated Data for Home Team ---")
    print(f"Last 5 Matches Avg Goals: {home_team.last_5_matches_avg_goals:.2f}")
    print(f"This Season Avg Goals: {home_team.this_season_avg_goals:.2f}")
    print(f"Total Avg Goals: {home_team.total_avg_goals:.2f}")
    print(f"Last 5 Matches Avg xG: {home_team.last_5_matches_avg_xg:.2f}")
    print(f"This Season Avg xG: {home_team.this_season_avg_xg:.2f}")
    print(f"Total Avg xG: {home_team.total_avg_xg:.2f}")
    print(f"Possession: {home_team.possession_percentage}, Passing Accuracy: {home_team.passing_accuracy}")
    print(f"Shots on Target: {home_team.shots_on_target}, Total Shots: {home_team.total_shots}")

    print("\n--- Aggregated Data for Away Team ---")
    print(f"Last 5 Matches Avg Goals: {away_team.last_5_matches_avg_goals:.2f}")
    print(f"This Season Avg Goals: {away_team.this_season_avg_goals:.2f}")
    print(f"Total Avg Goals: {away_team.total_avg_goals:.2f}")
    print(f"Last 5 Matches Avg xG: {away_team.last_5_matches_avg_xg:.2f}")
    print(f"This Season Avg xG: {away_team.this_season_avg_xg:.2f}")
    print(f"Total Avg xG: {away_team.total_avg_xg:.2f}")
    print(f"Possession: {away_team.possession_percentage}, Passing Accuracy: {away_team.passing_accuracy}")
    print(f"Shots on Target: {away_team.shots_on_target}, Total Shots: {away_team.total_shots}")

    # Calculate team strength from first eleven.
    home_first11, _ = pick_first_eleven(home_team)
    away_first11, _ = pick_first_eleven(away_team)
    home_first11_sum = sum(p.get_player_strength() for p in home_first11)
    away_first11_sum = sum(p.get_player_strength() for p in away_first11)

    home_final_power = home_first11_sum + synergy_home
    away_final_power = away_first11_sum + synergy_away

    print("\n--- Home Team Player Powers ---")
    for p in home_team.roster.players:
        power = p.get_player_strength()
        marker = "(First-11)" if p in home_first11 else "(Bench)"
        print(f"{p.player_name:<30}  Power={power:.2f} {marker}")

    print("\n--- Away Team Player Powers ---")
    for p in away_team.roster.players:
        power = p.get_player_strength()
        marker = "(First-11)" if p in away_first11 else "(Bench)"
        print(f"{p.player_name:<30}  Power={power:.2f} {marker}")

    print("\n=====================================================")
    print(f"Team {home_team.name} First 11 Sum: {home_first11_sum:.2f} + Synergy: {synergy_home:.2f} => Final: {home_final_power:.2f}")
    print(f"Team {away_team.name} First 11 Sum: {away_first11_sum:.2f} + Synergy: {synergy_away:.2f} => Final: {away_final_power:.2f}")
    print("=====================================================\n")

if __name__ == "__main__":
    main()