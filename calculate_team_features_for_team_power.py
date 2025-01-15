# server.py
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('soccerdata').setLevel(logging.CRITICAL)
logging.disable(logging.INFO)
import numpy as np

import pandas as pd
from understatapi import UnderstatClient

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import Ridge

from team_utils import (
    fill_last_5_matches_avg_goals,
    fill_this_season_avg_goals,
    fill_last_season_avg_goals,
    fill_total_avg_goals,
    fill_last_5_matches_avg_xg,
    fill_this_season_avg_xg,
    fill_last_season_avg_xg,
    fill_total_avg_xg,
)
from player_utils import (
    fill_last_5_matches_gk_stats,
    fill_this_season_gk_stats,
    fill_last_season_gk_stats,
    fill_total_gk_stats,
    fill_last_5_matches_avg_goals_and_xg,
    fill_season_avg_goals_and_xg,
    fill_total_avg_goals_and_xg,
    get_possession_percentage,
    get_passing_accuracy,
    get_shots_on_target,
    get_starting_eleven,
    get_last_match_formation,
    get_total_shots,
    guess_formation_from_lineup
)
from tactics import determine_team_formation, determine_team_play_style

understat = UnderstatClient()

class Player:
    def __init__(
        self,
        player_name,
        player_id,
        avg_shots=0.0,
        avg_fouls=0.0,
        avg_yellow_cards=0.0,
        avg_red_cards=0.0,
        avg_passes_completed=0.0,
        avg_rating=0.0,
        position="",
        avg_xg=0.0,
        avg_goals=0.0
    ):
        self.player_name = player_name
        self.player_id = player_id
        self.avg_shots = avg_shots
        self.avg_fouls = avg_fouls
        self.avg_yellow_cards = avg_yellow_cards
        self.avg_red_cards = avg_red_cards
        self.avg_passes_completed = avg_passes_completed
        self.avg_rating = avg_rating
        self.position = position
        self.avg_xg = avg_xg
        self.avg_goals = avg_goals

    def get_player_strength(self):
        """Return a weighted strength based on goals and xG."""
        return self.avg_goals * 0.7 + self.avg_xg * 0.3

class Roster:
    def __init__(self):
        self.players = []
    def add_player(self, player):
        self.players.append(player)

class Team:
    def __init__(self, name, short_title):
        self.name = name
        self.short_title = short_title
        self.last_5_matches_avg_goals = 0.0
        self.this_season_avg_goals = 0.0
        self.last_season_avg_goals = 0.0
        self.total_avg_goals = 0.0
        self.last_5_matches_avg_xg = 0.0
        self.this_season_avg_xg = 0.0
        self.last_season_avg_xg = 0.0
        self.total_avg_xg = 0.0
        self.matches = []
        self.roster = Roster()
        self.last_match_formation = None
        self.possession_percentage = None
        self.passing_accuracy = None
        self.shots_on_target = None
        self.total_shots = None
        self.formation = None
        self.style = None

    def get_match_data(self, season, understat):
        try:
            return understat.team(team=self.name).get_match_data(season=season)
        except Exception:
            return []

    def get_player_data(self, season, understat):
        try:
            return understat.team(team=self.name).get_player_data(season=season)
        except Exception:
            return []

    def get_goalkeeper_from_match(self, match, is_home):
        team_key = 'h' if is_home else 'a'
        team_players = match.get('players', {}).get(team_key, {})
        for player_id, player_data in team_players.items():
            if player_data.get('position') == 'GK':
                return {
                    'player_id': player_id,
                    'player': player_data.get('player', 'Unknown')
                }
        return None

    def fill_roster_with_player_data(self, season, understat):
        player_data = self.get_player_data(season, understat)
        for player_info in player_data:
            player_name = player_info.get('player_name')
            player_id = player_info.get('id')
            goals = float(player_info.get('goals', 0))
            games = float(player_info.get('games', 0))
            avg_goals = goals / games if games > 0 else 0.0

            avg_xg = float(player_info.get('xG', 0)) / games if games > 0 else 0.0
            avg_shots = float(player_info.get('shots', 0)) / games if games > 0 else 0.0
            avg_yellow_cards = float(player_info.get('yellow_cards', 0)) / games if games > 0 else 0.0
            avg_red_cards = float(player_info.get('red_cards', 0)) / games if games > 0 else 0.0
            position = player_info.get('position', "")

            if player_name and player_id:
                self.roster.add_player(Player(
                    player_name=player_name,
                    player_id=player_id,
                    avg_goals=avg_goals,
                    avg_xg=avg_xg,
                    avg_shots=avg_shots,
                    avg_yellow_cards=avg_yellow_cards,
                    avg_red_cards=avg_red_cards,
                    position=position
                ))
    def calculate_team_strength(self):
        """Calculate team's overall strength using a combination of factors."""
        team_strength = (self.total_avg_goals + self.total_avg_xg) / 2
        if self.passing_accuracy: team_strength += (self.passing_accuracy / 100) * 0.5
        if self.possession_percentage: team_strength += (self.possession_percentage / 100) * 0.5
        if self.shots_on_target: team_strength += (self.shots_on_target / 10)
        if self.total_shots: team_strength += (self.total_shots / 50)
        print(self.name)
        print(team_strength)
        return team_strength

    def get_top_scorers(self):
        """Get top players based on goals and xG."""
        return sorted(self.roster, key=lambda p: p.get_player_strength(), reverse=True)
    
import pandas as pd

def fill_this_season_avg_features(team):
    """Gather match data for the given teams across all seasons."""
    data = []
    count = 0

    # Adding all teams to the list

    matches = team.get_match_data("2025", understat)
    for match in matches:
        try:
            # Try to fetch match information
            match_info = understat.match(match["id"]).get_match_info()
            # Extract match information
            home_goals = match_info["h_goals"]
            away_goals = match_info["a_goals"]
            home_xg = match_info["h_xg"]
            away_xg = match_info["a_xg"]
            home_shots = match_info["h_shot"]
            away_shots = match_info["a_shot"]
            home_shots_on_target = match_info["h_shotOnTarget"]
            away_shots_on_target = match_info["a_shotOnTarget"]
            home_deep = match_info["h_deep"]
            away_deep = match_info["a_deep"]
            home_ppda = match_info["h_ppda"]
            away_ppda = match_info["a_ppda"]
            home_win_chances = match_info["h_w"]
            home_draw_chances = match_info["h_d"]
            home_loss_chances = match_info["h_l"]
            datetime = match_info["date"]
            team_home = match_info["team_h"]
            team_away = match_info["team_a"]
            
            # Store the extracted data (you can modify how it's stored or returned)
            data.append({
                "home_goals": home_goals,
                "away_goals": away_goals,
                "home_xg": home_xg,
                "away_xg": away_xg,
                "home_shots": home_shots,
                "away_shots": away_shots,
                "home_shots_on_target": home_shots_on_target,
                "away_shots_on_target": away_shots_on_target,
                "home_deep": home_deep,
                "away_deep": away_deep,
                "home_ppda": home_ppda,
                "away_ppda": away_ppda,
                "home_win_chances": home_win_chances,
                "home_draw_chances": home_draw_chances,
                "home_loss_chances": home_loss_chances,
                "datetime": datetime,
                "team_home": team_home,
                "team_away": team_away
            })
            
            count += 1
        
        except Exception as e:
            # Handle the error and print a message (can also log the error if needed)
            print(f"Error retrieving match info for match ID {match['id']}: {e}")
    print("count")

    print(count)
    return data
def calculate_liverpool_home_avg(data):
    """Calculate the average of features where Liverpool is the home team."""
    # Filter matches where Liverpool is the home team
    liverpool_home_matches = [match for match in data if match['team_home'] == 'Liverpool']
    
    # Initialize a dictionary to store the sum of each feature
    feature_sums = {
        "home_goals": 0,
        "away_goals": 0,
        "home_xg": 0,
        "away_xg": 0,
        "home_shots": 0,
        "away_shots": 0,
        "home_shots_on_target": 0,
        "away_shots_on_target": 0,
        "home_deep": 0,
        "away_deep": 0,
        "home_ppda": 0,
        "away_ppda": 0,
        "home_win_chances": 0,
        "home_draw_chances": 0,
        "home_loss_chances": 0
    }

    # Sum the features for each match where Liverpool is the home team
    for match in liverpool_home_matches:
        feature_sums["home_goals"] += float(match["home_goals"])
        feature_sums["away_goals"] += float(match["away_goals"])
        feature_sums["home_xg"] += float(match["home_xg"])
        feature_sums["away_xg"] += float(match["away_xg"])
        feature_sums["home_shots"] += float(match["home_shots"])
        feature_sums["away_shots"] += float(match["away_shots"])
        feature_sums["home_shots_on_target"] += float(match["home_shots_on_target"])
        feature_sums["away_shots_on_target"] += float(match["away_shots_on_target"])
        feature_sums["home_deep"] += float(match["home_deep"])
        feature_sums["away_deep"] += float(match["away_deep"])
        feature_sums["home_ppda"] += float(match["home_ppda"])
        feature_sums["away_ppda"] += float(match["away_ppda"])
        feature_sums["home_win_chances"] += float(match["home_win_chances"])
        feature_sums["home_draw_chances"] += float(match["home_draw_chances"])
        feature_sums["home_loss_chances"] += float(match["home_loss_chances"])

    # Calculate the average of each feature
    num_matches = len(liverpool_home_matches)
    if num_matches > 0:
        feature_averages = {key: value / num_matches for key, value in feature_sums.items()}
    else:
        feature_averages = {}

    return feature_averages

def calculate_chelsea_away_avg(data):
    """Calculate the average of features where Liverpool is the home team."""
    # Filter matches where Liverpool is the home team
    liverpool_home_matches = [match for match in data if match['team_away'] == 'Chelsea']
    
    # Initialize a dictionary to store the sum of each feature
    feature_sums = {
        "home_goals": 0,
        "away_goals": 0,
        "home_xg": 0,
        "away_xg": 0,
        "home_shots": 0,
        "away_shots": 0,
        "home_shots_on_target": 0,
        "away_shots_on_target": 0,
        "home_deep": 0,
        "away_deep": 0,
        "home_ppda": 0,
        "away_ppda": 0,
        "home_win_chances": 0,
        "home_draw_chances": 0,
        "home_loss_chances": 0
    }

    # Sum the features for each match where Liverpool is the home team
    for match in liverpool_home_matches:
        feature_sums["home_goals"] += float(match["home_goals"])
        feature_sums["away_goals"] += float(match["away_goals"])
        feature_sums["home_xg"] += float(match["home_xg"])
        feature_sums["away_xg"] += float(match["away_xg"])
        feature_sums["home_shots"] += float(match["home_shots"])
        feature_sums["away_shots"] += float(match["away_shots"])
        feature_sums["home_shots_on_target"] += float(match["home_shots_on_target"])
        feature_sums["away_shots_on_target"] += float(match["away_shots_on_target"])
        feature_sums["home_deep"] += float(match["home_deep"])
        feature_sums["away_deep"] += float(match["away_deep"])
        feature_sums["home_ppda"] += float(match["home_ppda"])
        feature_sums["away_ppda"] += float(match["away_ppda"])
        feature_sums["home_win_chances"] += float(match["home_win_chances"])
        feature_sums["home_draw_chances"] += float(match["home_draw_chances"])
        feature_sums["home_loss_chances"] += float(match["home_loss_chances"])

    # Calculate the average of each feature
    num_matches = len(liverpool_home_matches)
    if num_matches > 0:
        feature_averages = {key: value / num_matches for key, value in feature_sums.items()}
    else:
        feature_averages = {}

    return feature_averages
# Main function to load data and perform the necessary calculations
def main():
    liverpool = Team("Liverpool", "LIV")
    average_features = fill_this_season_avg_features(liverpool)
    print("Average home match features for Liverpool in the 2025 season:")
    avg = calculate_liverpool_home_avg(average_features)
    print(avg)

    chelsea = Team("Chelsea", "CHE")
    average_features = fill_this_season_avg_features(chelsea)
    print("Average home match features for Chelsea in the 2025 season:")
    avg = calculate_chelsea_away_avg(average_features)
    print(avg)

if __name__ == "__main__":
    main()