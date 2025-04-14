#!/usr/bin/env python3
"""
match_power_calculator.py

Revised version for calculating team and player power based on advanced data:
- Uses API-Football to fetch upcoming fixtures.
- Uses UnderstatClient (from understatapi) to fetch match-by-match data.
- Aggregates season, recent, and career stats for each player.
- Computes a player power score with advanced weightings (e.g. goals and xG),
  and then sums the power of the first eleven players plus a synergy bonus.
- Prints all incoming aggregated data for debugging.
"""

import logging
import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta

from player_utils import get_passing_accuracy, get_possession_percentage, get_shots_on_target, get_total_shots

# -----------------------------
# 1) API-Football Setup (Fixtures)
# -----------------------------
BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",    # Replace with your real key
    "x-apisports-host": "v3.football.api-sports.io"
}
LEAGUE_ID = 39  # Premier League
SEASON = "2024"

def fetch_fixtures_in_7_days(league_id=LEAGUE_ID, season=SEASON):
    """
    Fetch fixtures that occur exactly 7 days from now.
    Returns a list of fixture dicts.
    """
    target_date = date.today() + timedelta(days=7)
    date_str = target_date.isoformat()
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}&from={date_str}&to={date_str}"
    resp = requests.get(url, headers=API_HEADERS)
    data = resp.json()
    fixtures_list = []
    if data.get("response"):
        for item in data["response"]:
            fix = item["fixture"]
            teams = item["teams"]
            fixtures_list.append({
                "fixture_id": fix["id"],
                "date": fix["date"],
                "home_team_name": teams["home"]["name"],
                "away_team_name": teams["away"]["name"]
            })
    return fixtures_list

# -----------------------------
# 2) UnderstatClient Import
# -----------------------------
from understatapi import UnderstatClient

# -----------------------------
# 3) Data Classes with Advanced Player Power Calculation
# -----------------------------
class Player:
    def __init__(self, player_name, player_id, avg_goals=0.0, avg_xg=0.0, position=""):
        self.player_name = player_name
        self.player_id = player_id
        self.avg_goals = avg_goals
        self.avg_xg = avg_xg
        self.position = position
        # You can later add additional attributes from other metrics.
        self.player_power = 0.0

    def get_player_strength(self):
        """
        Advanced player power calculation for demonstration.
        For now we combine average goals and average xG with custom weights.
        (Forwards, for example, might have 5x weight on goals and 3x weight on xG.)
        For other positions you can adjust the weights accordingly.
        
        Additionally, we print out the underlying data for debugging.
        """
        # Example weight configuration by position:
        pos = self.position.upper()
        if pos in ["F", "FW", "LW", "RW"]:
            weight_goals = 5.0
            weight_xg = 3.0
        elif pos in ["M", "CM", "AM", "DM"]:
            weight_goals = 3.0
            weight_xg = 3.0
        elif pos in ["D", "CB", "LB", "RB"]:
            weight_goals = 2.0
            weight_xg = 1.0
        elif pos in ["G", "GK"]:
            weight_goals = 0.0
            weight_xg = 0.0
        else:
            weight_goals = 3.0
            weight_xg = 3.0

        # Debug: show underlying stats.
        logging.debug(f"Calculating power for {self.player_name}: avg_goals={self.avg_goals}, avg_xG={self.avg_xg}, position={self.position}")
        self.player_power = (self.avg_goals * weight_goals) + (self.avg_xg * weight_xg)
        return self.player_power

class Roster:
    def __init__(self):
        self.players = []
    def add_player(self, player):
        self.players.append(player)

class Team:
    def __init__(self, name, short_title):
        self.name = name
        self.short_title = short_title
        # Aggregated Understat data (goals, xG)
        self.last_5_matches_avg_goals = 0.0
        self.this_season_avg_goals = 0.0
        self.last_season_avg_goals = 0.0
        self.total_avg_goals = 0.0
        self.last_5_matches_avg_xg = 0.0
        self.this_season_avg_xg = 0.0
        self.last_season_avg_xg = 0.0
        self.total_avg_xg = 0.0
        self.matches = []  # Understat match data will be stored here.
        self.roster = Roster()
        # FBref stats (set as dummy here or use real calls from soccerdata)
        self.possession_percentage = None
        self.passing_accuracy = None
        self.shots_on_target = None
        self.total_shots = None
        # Formation and style data
        self.last_match_formation = None
        self.formation = None
        self.style = None

    # Understat data fetchers:
    def get_match_data(self, season, understat: UnderstatClient):
        try:
            return understat.team(team=self.name).get_match_data(season=season)
        except Exception as e:
            logging.error(f"Error getting match data for team {self.name}: {e}")
            return []

    def get_player_data(self, season, understat: UnderstatClient):
        try:
            return understat.team(team=self.name).get_player_data(season=season)
        except Exception as e:
            logging.error(f"Error getting player data for team {self.name}: {e}")
            return []

    def fill_roster_with_player_data(self, season, understat: UnderstatClient):
        """
        Creates Player objects for the team using Understat's player data.
        For demonstration, we use only avg_goals and avg_xg from Understat.
        """
        data = self.get_player_data(season, understat)
        for p in data:
            pname = p.get('player_name')
            pid = p.get('id')
            # Calculate per-match averages:
            g = float(p.get('goals', 0))
            gm = float(p.get('games', 0))
            avg_g = g / gm if gm > 0 else 0.0
            avg_x = float(p.get('xG', 0))
            avg_xg = avg_x / gm if gm > 0 else 0.0
            pos = p.get('position', "")
            if pname and pid:
                new_player = Player(player_name=pname, player_id=pid, avg_goals=avg_g, avg_xg=avg_xg, position=pos)
                self.roster.add_player(new_player)

    def calculate_team_strength(self):
        """
        For demonstration, the team's base strength is calculated as the sum of the
        first eleven players' power.
        """
        first11, _ = pick_first_eleven(self)
        if not first11:
            return 0.0
        total = sum(player.get_player_strength() for player in first11)
        return total

# -----------------------------
# 4) Understat Data Aggregation Functions
# -----------------------------



def fill_this_season_avg_goals(team: Team, season: str, understat: UnderstatClient):
    """Aggregate average goals from all matches in the current season."""
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "goals" in m:
            if m["h"]["short_title"] == team.short_title:
                x = m["goals"].get("h")
                if x is not None:
                    arr.append(int(x))
            elif m["a"]["short_title"] == team.short_title:
                x = m["goals"].get("a")
                if x is not None:
                    arr.append(int(x))
    team.this_season_avg_goals = np.mean(arr) if arr else 0.0
    logging.debug(f"This season avg goals for {team.name}: {team.this_season_avg_goals}")

def fill_total_avg_goals(team: Team):
    """Aggregate average goals from all matches in team.matches."""
    arr = []
    for m in team.matches:
        if "goals" in m:
            if m["h"]["short_title"] == team.short_title:
                x = m["goals"].get("h")
                if x is not None:
                    arr.append(int(x))
            elif m["a"]["short_title"] == team.short_title:
                x = m["goals"].get("a")
                if x is not None:
                    arr.append(int(x))
    team.total_avg_goals = np.mean(arr) if arr else 0.0
    logging.debug(f"Total avg goals for {team.name}: {team.total_avg_goals}")


def fill_this_season_avg_xg(team: Team, season: str, understat: UnderstatClient):
    """Aggregate average xG from all matches in the current season."""
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v:
                    arr.append(float(v))
    team.this_season_avg_xg = np.mean(arr) if arr else 0.0
    logging.debug(f"This season avg xG for {team.name}: {team.this_season_avg_xg}")

def fill_total_avg_xg(team: Team):
    """Aggregate average xG from all matches in team.matches."""
    arr = []
    for m in team.matches:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v:
                    arr.append(float(v))
    team.total_avg_xg = np.mean(arr) if arr else 0.0
    logging.debug(f"Total avg xG for {team.name}: {team.total_avg_xg}")

def fill_all_stats(team: Team, current_season: str, last_season: str, all_seasons: list, understat: UnderstatClient):
    """
    Gathers all data for a team:
      - Fetches match data for all seasons (adds to team.matches)
      - Aggregates goals and xG (last 5, current season, last season, total)
      - Fills the team roster from Understat player data.
      - Sets FBref stats (dummy placeholders).
      - Determines a formation if missing.
    """
    # Gather match data from all seasons
    for s in all_seasons:
        team.matches.extend(team.get_match_data(s, understat))

    # Goals
    fill_this_season_avg_goals(team, current_season, understat)
    # For simplicity, skipping last season separately
    fill_total_avg_goals(team)

    # xG
    fill_this_season_avg_xg(team, current_season, understat)
    fill_total_avg_xg(team)

    # Roster from Understat
    team.fill_roster_with_player_data(current_season, understat)

    # FBref-like stats (using dummy values here)
    team.possession_percentage = get_possession_percentage(team.name, current_season)
    team.passing_accuracy = get_passing_accuracy(team.name, current_season)
    team.shots_on_target = get_shots_on_target(team.name, current_season)
    team.total_shots = get_total_shots(team.name, current_season)

    # Formation fallback
    if not team.last_match_formation:
        team.last_match_formation = "4-3-3"

# -----------------------------
# 5) Formation & Style Determination
# -----------------------------
from datetime import date, timedelta
API_FOOTBALL_KEY = "078dfd2522b94892b4675b57bd810999"  # Replace with your key
API_FOOTBALL_HOST = "v3.football.api-sports.io"
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39
CURRENT_SEASON = "2024"
LAST_SEASON = "2023"

def fetch_fixtures_in_range(league_id=LEAGUE_ID, season=CURRENT_SEASON, days_back=2, days_forward=2):
    logging.debug("Fetching fixtures from API‑Football")
    start_date = (date.today() - timedelta(days=days_back)).isoformat()
    end_date = (date.today() + timedelta(days=days_forward)).isoformat()
    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}&from={start_date}&to={end_date}"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
        "x-apisports-host": API_FOOTBALL_HOST
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        logging.error(f"Error fetching fixtures: {e}")
        return []
    fixtures_list = []
    if data.get("response"):
        for item in data["response"]:
            fix = item["fixture"]
            teams = item["teams"]
            fixtures_list.append({
                "fixture_id": fix["id"],
                "date": fix["date"],
                "home_team_name": teams["home"]["name"],
                "away_team_name": teams["away"]["name"]
            })
    logging.debug(f"Fetched {len(fixtures_list)} fixtures")
    return fixtures_list

def determine_team_formation(team: Team):
    if team.last_match_formation:
        return team.last_match_formation
    return "Unknown Formation"

def determine_team_play_style(team: Team):
    if team.possession_percentage > 60 and team.passing_accuracy > 85:
        return "Possession Based"
    elif team.possession_percentage < 45 and team.shots_on_target >= 8:
        return "Counter Attack"
    else:
        return "Balanced"

# -----------------------------
# 6) Synergy Calculation
# -----------------------------
def synergy_from_formation_style(formA, styA, formB, styB, history_df):
    sub = history_df.loc[
        ((history_df["Formation_home"] == formA) &
         (history_df["style_home"] == styA) &
         (history_df["Formation_away"] == formB) &
         (history_df["style_away"] == styB))
        |
        ((history_df["Formation_home"] == formB) &
         (history_df["style_home"] == styB) &
         (history_df["Formation_away"] == formA) &
         (history_df["style_away"] == styA))
    ]
    sub = sub.tail(10)
    if sub.empty:
        return (0.0, 0.0)
    a_bonus = 0.0
    b_bonus = 0.0
    for _, row in sub.iterrows():
        hg = row["goals_home"]
        ag = row["goals_away"]
        if hg > ag:
            if row["Formation_home"] == formA and row["style_home"] == styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3
        elif ag > hg:
            if row["Formation_away"] == formA and row["style_away"] == styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3
    return (a_bonus, b_bonus)

# -----------------------------
# 7) First Eleven Selection
# -----------------------------
def pick_first_eleven(team: Team):
    sorted_by_power = sorted(team.roster.players, key=lambda p: p.get_player_strength(), reverse=True)
    first_11 = sorted_by_power[:11]
    bench = sorted_by_power[11:]
    return first_11, bench

# -----------------------------
# 8) Main Routine: Data and Power Calculation
# -----------------------------
def main():
    # Fetch fixtures happening in EXACT 7 days.
    upcoming = fetch_fixtures_in_range()
    if not upcoming:
        print("No fixtures found exactly 7 days from now.")
        return

    print("\nFixtures in EXACT 7 days:\n")
    for i, fix in enumerate(upcoming):
        dt_str = fix["date"].replace("T"," ")[:16]
        print(f"[{i}] FixtureID={fix['fixture_id']}  {dt_str}  {fix['home_team_name']} vs {fix['away_team_name']}")

    choice = input("\nSelect a fixture index to analyze: ")
    try:
        idx = int(choice)
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

    # Seasons for stats.
    current_season = "2024"
    last_season = "2023"
    all_seasons = ["2023", "2024"]

    # Load synergy history from file.
    history_file = "history_df.xlsx"
    try:
        history_df = pd.read_excel(history_file)
    except Exception as e:
        print(f"Warning: could not load synergy file '{history_file}': {e}")
        history_df = pd.DataFrame()

    # Fill team stats using Understat.
    with UnderstatClient() as understat:
        # Fill match data, aggregated stats, and roster.
        fill_all_stats(home_team, current_season, last_season, all_seasons, understat)
        fill_all_stats(away_team, current_season, last_season, all_seasons, understat)

    # Determine formation & style.
    home_team.formation = determine_team_formation(home_team)
    home_team.style = "determine_team_play_style(home_team)"
    away_team.formation = determine_team_formation(away_team)
    away_team.style = determine_team_play_style(away_team)

    # Print out all aggregated data for debugging.
    print("\n--- Aggregated Data for Home Team ---")
    print(f"Last 5 Matches Avg Goals: {home_team.last_5_matches_avg_goals}")
    print(f"This Season Avg Goals: {home_team.this_season_avg_goals}")
    print(f"Total Avg Goals: {home_team.total_avg_goals}")
    print(f"Last 5 Matches Avg xG: {home_team.last_5_matches_avg_xg}")
    print(f"This Season Avg xG: {home_team.this_season_avg_xg}")
    print(f"Total Avg xG: {home_team.total_avg_xg}")
    print(f"Possession: {home_team.possession_percentage}, Passing Accuracy: {home_team.passing_accuracy}")
    print(f"Shots on Target: {home_team.shots_on_target}, Total Shots: {home_team.total_shots}")

    print("\n--- Aggregated Data for Away Team ---")
    print(f"Last 5 Matches Avg Goals: {away_team.last_5_matches_avg_goals}")
    print(f"This Season Avg Goals: {away_team.this_season_avg_goals}")
    print(f"Total Avg Goals: {away_team.total_avg_goals}")
    print(f"Last 5 Matches Avg xG: {away_team.last_5_matches_avg_xg}")
    print(f"This Season Avg xG: {away_team.this_season_avg_xg}")
    print(f"Total Avg xG: {away_team.total_avg_xg}")
    print(f"Possession: {away_team.possession_percentage}, Passing Accuracy: {away_team.passing_accuracy}")
    print(f"Shots on Target: {away_team.shots_on_target}, Total Shots: {away_team.total_shots}")

    # Calculate base team strength using our revised method (sum of first 11 player powers).
    home_first11, _ = pick_first_eleven(home_team)
    away_first11, _ = pick_first_eleven(away_team)
    home_first11_sum = sum(p.get_player_strength() for p in home_first11)
    away_first11_sum = sum(p.get_player_strength() for p in away_first11)

    # Determine synergy bonus.
    synergy_home, synergy_away = synergy_from_formation_style(
        home_team.formation or "Unknown Formation",
        home_team.style or "Balanced",
        away_team.formation or "Unknown Formation",
        away_team.style or "Balanced",
        history_df
    )

    # Final team power: sum of first 11 players plus synergy.
    home_final_power = home_first11_sum + synergy_home
    away_final_power = away_first11_sum + synergy_away

    # Print out individual player power values.
    print("\n--- Home Team Player Powers ---")
    for p in home_team.roster.players:
        power = p.get_player_strength()
        marker = "(First-11)" if p in home_first11 else "(Bench)"
        print(f"{p.player_name:<20}  Power={power:.2f} {marker}")

    print("\n--- Away Team Player Powers ---")
    for p in away_team.roster.players:
        power = p.get_player_strength()
        marker = "(First-11)" if p in away_first11 else "(Bench)"
        print(f"{p.player_name:<20}  Power={power:.2f} {marker}")

    print("\n=====================================================")
    print(f"Team {home_team.name} First 11 Sum: {home_first11_sum:.2f} + Synergy: {synergy_home:.2f} => Final: {home_final_power:.2f}")
    print(f"Team {away_team.name} First 11 Sum: {away_first11_sum:.2f} + Synergy: {synergy_away:.2f} => Final: {away_final_power:.2f}")
    print("=====================================================\n")

if __name__ == "__main__":
    main()