# history_creator_all_teams.py

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('soccerdata').setLevel(logging.CRITICAL)
logging.disable(logging.INFO)

import pandas as pd
import numpy as np
import time

from utils import UnderstatClient , sd  # Ensure your utils.py has UnderstatClient and 'import soccerdata as sd'
from player_utils import (
    get_passing_accuracy,
    get_shots_on_target,
    get_possession_percentage,
    get_total_shots,
    get_last_match_formation,
    get_starting_eleven,
    guess_formation_from_lineup
)

##############################################
# List of EPL Teams and Helper to Create Slugs
##############################################

EPL_TEAMS = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Liverpool", "Luton Town", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Sheffield United",
    "Tottenham", "West Ham", "Wolves"
]

def team_slug(team):
    return team.lower().replace(" ", "-")

##############################################
# Helper: Extract Teams from match_report URL
##############################################

def extract_teams_from_matchreport(row):
    """
    Extracts home and away team names from the match_report URL.
    The URL is assumed to be in the form:
      /en/matches/<id>/<home-team>-<away-team>-...
    We search for known EPL team slugs in the URL and return (home_team, away_team).
    If not found, returns ("Unknown", "Unknown").
    """
    mr = row.get("match_report", "")
    if not isinstance(mr, str) or not mr:
        return ("Unknown", "Unknown")
    mr_lower = mr.lower()
    found = []
    for team in EPL_TEAMS:
        slug = team_slug(team)
        pos = mr_lower.find(slug)
        if pos != -1:
            found.append((pos, team))
    found.sort(key=lambda x: x[0])
    if len(found) >= 2:
        return (found[0][1], found[1][1])
    else:
        return ("Unknown", "Unknown")

##############################################
# Simple Team Class (for style determination)
##############################################

class Team:
    def __init__(self, name, season):
        self.name = name
        self.season = season
        self.possession_percentage = None
        self.shots_on_target = None
        self.passing_accuracy = None
        self.total_shots = None

##############################################
# Style functions
##############################################

def style_counter_attack(team):
    if team.possession_percentage is not None and team.possession_percentage < 45:
        if team.shots_on_target is not None and team.shots_on_target >= 5:
            return True
    return False

def style_possession_based(team):
    if team.possession_percentage is not None and team.possession_percentage > 60:
        if team.shots_on_target is not None and team.shots_on_target >= 10:
            if team.passing_accuracy is not None and team.passing_accuracy > 85:
                return True
    return False

def style_high_press(team):
    if team.possession_percentage is not None and team.possession_percentage > 50:
        if team.shots_on_target is not None and team.shots_on_target >= 12:
            if team.passing_accuracy is not None and team.passing_accuracy > 80:
                return True
    return False

def style_low_press(team):
    if team.possession_percentage is not None and team.possession_percentage < 50:
        if team.shots_on_target is not None and team.shots_on_target >= 8:
            if team.passing_accuracy is not None and team.passing_accuracy < 75:
                return True
    return False

def style_fast_break(team):
    if team.possession_percentage is not None and team.possession_percentage < 45:
        if team.shots_on_target is not None and team.shots_on_target >= 9:
            return True
    return False

def style_ball_control(team):
    if team.possession_percentage is not None and team.possession_percentage > 55:
        if team.shots_on_target is not None and team.shots_on_target >= 10:
            if team.passing_accuracy is not None and team.passing_accuracy > 83:
                return True
    return False

def style_flank_attack(team):
    if team.possession_percentage is not None and team.possession_percentage > 55:
        if team.shots_on_target is not None and team.shots_on_target >= 10:
            if team.total_shots is not None and team.total_shots >= 15:
                return True
    return False

def style_midfield_control(team):
    if team.possession_percentage is not None and team.possession_percentage > 60:
        if team.shots_on_target is not None and team.shots_on_target >= 10:
            if team.passing_accuracy is not None and team.passing_accuracy > 85:
                return True
    return False

def style_direct_play(team):
    if team.possession_percentage is not None and team.possession_percentage < 50:
        if team.shots_on_target is not None and team.shots_on_target >= 8:
            if team.passing_accuracy is not None and team.passing_accuracy < 80:
                return True
    return False

def style_territorial(team):
    if team.possession_percentage is not None and team.possession_percentage > 50:
        if team.shots_on_target is not None and team.shots_on_target >= 9:
            if team.passing_accuracy is not None and team.passing_accuracy > 80:
                return True
    return False

def style_park_the_bus(team):
    if team.possession_percentage is not None and team.possession_percentage < 35:
        if team.shots_on_target is not None and team.shots_on_target < 5:
            return True
    return False

def style_gengenpress(team):
    if team.possession_percentage is not None and team.possession_percentage > 50:
        if team.shots_on_target is not None and team.shots_on_target >= 12:
            if team.passing_accuracy is not None and team.passing_accuracy > 75:
                if team.total_shots is not None and team.total_shots >= 18:
                    return True
    return False

def style_long_ball(team):
    if team.possession_percentage is not None and team.possession_percentage < 45:
        if team.shots_on_target is not None and team.shots_on_target >= 7:
            if team.passing_accuracy is not None and team.passing_accuracy < 78:
                return True
    return False

def style_tiki_taka(team):
    if team.possession_percentage is not None and team.possession_percentage > 65:
        if team.passing_accuracy is not None and team.passing_accuracy > 88:
            if team.shots_on_target is not None and team.shots_on_target >= 10:
                return True
    return False

def style_defensive_solid(team):
    if team.possession_percentage is not None and team.possession_percentage < 40:
        if team.shots_on_target is not None and team.shots_on_target >= 6:
            if team.total_shots is not None and team.total_shots < 12:
                return True
    return False

def style_wing_play(team):
    if team.possession_percentage is not None and team.possession_percentage > 50:
        if team.shots_on_target is not None and team.shots_on_target >= 8:
            if team.total_shots is not None and team.total_shots >= 16:
                if team.passing_accuracy is not None and team.passing_accuracy > 80:
                    return True
    return False

def style_overload_midfield(team):
    if team.possession_percentage is not None and team.possession_percentage > 55:
        if team.shots_on_target is not None and team.shots_on_target >= 11:
            if team.passing_accuracy is not None and 40 < team.passing_accuracy < 90:
                if team.total_shots is not None and team.total_shots >= 14:
                    return True
    return False

def style_slow_build_up(team):
    if team.possession_percentage is not None and team.possession_percentage > 50:
        if team.shots_on_target is not None and team.shots_on_target >= 8:
            if team.passing_accuracy is not None and team.passing_accuracy > 82:
                if team.total_shots is not None and team.total_shots < 15:
                    return True
    return False

def style_direct_counter(team):
    if team.possession_percentage is not None and team.possession_percentage < 45:
        if team.shots_on_target is not None and team.shots_on_target >= 10:
            if team.passing_accuracy is not None and team.passing_accuracy < 80:
                return True
    return False

def style_clinical_finishing(team):
    if team.shots_on_target is not None and team.shots_on_target >= 12:
        if team.total_shots is not None and team.total_shots <= 16:
            if team.possession_percentage is not None and 40 < team.possession_percentage < 60:
                return True
    return False

def compute_style(team: Team) -> str:
    if style_counter_attack(team):
        return "Counter Attack"
    elif style_possession_based(team):
        return "Possession Based"
    elif style_high_press(team):
        return "High Press"
    elif style_low_press(team):
        return "Low Press"
    elif style_fast_break(team):
        return "Fast Break"
    elif style_ball_control(team):
        return "Ball Control"
    elif style_flank_attack(team):
        return "Flank Attack"
    elif style_midfield_control(team):
        return "Midfield Control"
    elif style_direct_play(team):
        return "Direct Play"
    elif style_territorial(team):
        return "Territorial"
    elif style_park_the_bus(team):
        return "Park The Bus"
    elif style_gengenpress(team):
        return "Gegenpress"
    elif style_long_ball(team):
        return "Long Ball"
    elif style_tiki_taka(team):
        return "Tiki Taka"
    elif style_defensive_solid(team):
        return "Defensive Solid"
    elif style_wing_play(team):
        return "Wing Play"
    elif style_overload_midfield(team):
        return "Overload Midfield"
    elif style_slow_build_up(team):
        return "Slow Build Up"
    elif style_direct_counter(team):
        return "Direct Counter"
    elif style_clinical_finishing(team):
        return "Clinical Finishing"
    else:
        return "Balanced"

##############################################
# Main: Build history_df.xlsx for synergy usage
##############################################

def main():
    start_time = time.time()
    
    # Define seasons to process. (Adjust as desired)
    seasons = ["2019-2020", "2020-2021", "2021-2022", "2022-2023","2023-2024","2024-2025"]
    frames = []
    
    for season in seasons:
        fb = sd.FBref(leagues=["ENG-Premier League"], seasons=[season])
        df = fb.read_team_match_stats(stat_type="schedule")
        df = df.reset_index(drop=True)
        
        # Rename columns for consistency
        cols_lower = [col.lower() for col in df.columns]
        rename_dict = {}
        for orig, new in [("date", "Date"), ("opponent", "Opponent"),
                          ("formation", "Formation"), ("opp formation", "Opp Formation"),
                          ("venue", "Venue"), ("match_report", "match_report"),
                          ("gf", "GF"), ("ga", "GA")]:
            if orig in cols_lower and new not in df.columns:
                for col in df.columns:
                    if col.lower() == orig:
                        rename_dict[col] = new
                        break
        df = df.rename(columns=rename_dict)
        df["Season"] = season
        frames.append(df)
    
    data = pd.concat(frames, ignore_index=True)
    
    # Identify the Date column
    date_cols = [c for c in data.columns if "date" in c.lower()]
    if not date_cols:
        print("No date column found!")
        return
    date_col = date_cols[0]
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")

    # Attempt to extract teams if "Team" column is missing
    if not any(c.lower() == "team" for c in data.columns):
        print("Column 'Team' not found. Extracting team names from match_report...")
        data[["team_home", "team_away"]] = data.apply(
            lambda row: pd.Series(extract_teams_from_matchreport(row)),
            axis=1
        )
    else:
        # If we do have a 'Team' column, treat it as 'team_home' & 'Opponent' as 'team_away'
        data["team_home"] = data["Team"]
        data["team_away"] = data["Opponent"]
    
    # Remove records where either team is "Unknown"
    data = data[(data["team_home"] != "Unknown") & (data["team_away"] != "Unknown")]
    
    # Create Formation_home, Formation_away from the venue perspective
    data["Formation_home"] = np.where(
        data["Venue"].str.lower() == "home",
        data["Formation"],
        data["Opp Formation"]
    )
    data["Formation_away"] = np.where(
        data["Venue"].str.lower() == "home",
        data["Opp Formation"],
        data["Formation"]
    )
    # Drop missing/unknown formation
    data = data[data["Formation_home"].notna() & data["Formation_away"].notna()]
    data = data[(data["Formation_home"] != "Unknown Formation") & (data["Formation_away"] != "Unknown Formation")]
    
    # Goals based on venue
    data["goals_home"] = np.where(
        data["Venue"].str.lower() == "home",
        data["GF"],
        data["GA"]
    )
    data["goals_away"] = np.where(
        data["Venue"].str.lower() == "home",
        data["GA"],
        data["GF"]
    )
    
    # Cache (team, season) stats for speed
    stat_cache = {}
    def get_team_stat(team_name, season, func):
        key = (team_name, season)
        if key not in stat_cache:
            stat_cache[key] = {}
        if func.__name__ not in stat_cache[key]:
            stat_cache[key][func.__name__] = func(team_name, season)
        return stat_cache[key][func.__name__]
    
    history_records = []
    for idx, row in data.iterrows():
        season = row.get("Season", "Unknown")
        team_home_name = row.get("team_home", "Unknown")
        team_away_name = row.get("team_away", "Unknown")
        formation_home = row.get("Formation_home", "Unknown Formation")
        formation_away = row.get("Formation_away", "Unknown Formation")
        goals_home = row.get("goals_home", 0)
        goals_away = row.get("goals_away", 0)
        
        home_team = Team(team_home_name, season)
        away_team = Team(team_away_name, season)
        
        # Gather stats from your player_utils functions
        home_team.possession_percentage = get_team_stat(team_home_name, season, get_possession_percentage) or 50
        home_team.shots_on_target       = get_team_stat(team_home_name, season, get_shots_on_target) or 10
        home_team.passing_accuracy      = get_team_stat(team_home_name, season, get_passing_accuracy) or 80
        home_team.total_shots           = get_team_stat(team_home_name, season, get_total_shots) or 15
        
        away_team.possession_percentage = get_team_stat(team_away_name, season, get_possession_percentage) or 50
        away_team.shots_on_target       = get_team_stat(team_away_name, season, get_shots_on_target) or 10
        away_team.passing_accuracy      = get_team_stat(team_away_name, season, get_passing_accuracy) or 80
        away_team.total_shots           = get_team_stat(team_away_name, season, get_total_shots) or 15
        
        style_home = compute_style(home_team)
        style_away = compute_style(away_team)
        
        history_records.append({
            "Season": season,
            date_col: row[date_col],
            "team_home": team_home_name,
            "Formation_home": formation_home,
            "style_home": style_home,
            "team_away": team_away_name,
            "Formation_away": formation_away,
            "style_away": style_away,
            "goals_home": goals_home,
            "goals_away": goals_away
        })
    
    history_df = pd.DataFrame(history_records).sort_values(by=date_col)
    history_df = history_df.drop_duplicates()  # remove duplicates if any
    
    # Save to Excel
    output_filename = "history_df.xlsx"
    history_df.to_excel(output_filename, index=False)
    
    print(f"\nCreated '{output_filename}' with {len(history_df)} rows.")
    print("Elapsed time: {:.2f} seconds".format(time.time() - start_time))

if __name__ == "__main__":
    main()