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
    
def safe_convert_formation(formation):
    if pd.isna(formation):
        return None
    return formation

def game_theory_prediction(team1, team2):
    """Simulate the match using game theory concepts."""
    team1_strength = team1.calculate_team_strength()
    team2_strength = team2.calculate_team_strength()

    # Consider formation and play style adjustments
    if team1.style == "High Press" and team2.style == "Low Press":
        team1_strength += 1
    elif team2.style == "High Press" and team1.style == "Low Press":
        team2_strength += 1

    # Simulate match score prediction
    score_diff = team1_strength - team2_strength
    avg_goals_factor = (team1.total_avg_goals + team2.total_avg_goals) / 2
    avg_goals_factor = max(avg_goals_factor, 1.0)

    team1_goals = avg_goals_factor + (score_diff * 0.5)
    team2_goals = avg_goals_factor - (score_diff * 0.5)

    return int(round(team1_goals)), int(round(team2_goals))

import pandas as pd

def gather_match_data():
    all_seasons = [str(year) for year in range(2017, 2024)]

    # Teams initialization
    arsenal = Team("Arsenal", "ARS")
    brighton = Team("Brighton", "BHA")
    chelsea = Team("Chelsea", "CHE")
    crystal_palace = Team("Crystal Palace", "CRY")
    everton = Team("Everton", "EVE")
    liverpool = Team("Liverpool", "LIV")
    man_city = Team("Manchester City", "MCI")
    man_united = Team("Manchester_United", "MUN")
    newcastle = Team("Newcastle United", "NEW")
    tottenham = Team("Tottenham", "TOT")
    west_ham = Team("West Ham", "WHU")

    # Adding all teams to the list
    teams = [
        arsenal, brighton, chelsea, crystal_palace, everton, liverpool, man_city, man_united, newcastle, tottenham, west_ham
    ]

    """Gather match data for the given teams across all seasons."""
    data = []
    count = 0
    for team in teams:
        for season in all_seasons:
            matches = team.get_match_data(season, understat)
            print(count)
            for match in matches:
                match_info = understat.match(match["id"]).get_match_info()
                count = count + 1
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

                # Append match data to the list
                data.append({
                    "match_id": match_info["id"],
                    "team": team.name,
                    "home": team_home,
                    "away": team_away,
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
                })
    
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)
    
    # Remove duplicate matches by match_id
    df = df.drop_duplicates(subset="match_id").reset_index(drop=True)

    # Save the data to an Excel file
    df.to_excel("match_data.xlsx", index=False)
    print("Match data saved to match_data.xlsx")
    
    return df

# Function to calculate coefficients using linear regression
def calculate_coefficients(data, features, target):
    model = LinearRegression()
    
    # Prepare features and target for regression
    X = data[features]
    y = data[target]
    
    # Fit the model
    model.fit(X, y)
    
    # Get the coefficients and intercept
    coefficients = model.coef_
    intercept = model.intercept_

    return coefficients, intercept

# Function to calculate home and away team power
def calculate_team_power(home_stats, away_stats, home_coefficients, home_intercept, away_coefficients, away_intercept):
    home_power = home_intercept + np.dot(home_coefficients, home_stats)
    away_power = away_intercept + np.dot(away_coefficients, away_stats)
    return home_power, away_power

# Main function to load data and perform the necessary calculations
def main():

    #gather_match_data()
    # Load the match data
    df = pd.read_excel("match_data.xlsx")
    
    # Define features for regression (removing goals and xG, for simplicity)
    home_features = ['home_shots', 'home_shots_on_target', 'home_deep', 
                     'home_ppda', 'home_win_chances', 'home_draw_chances']
    away_features = ['away_shots', 'away_shots_on_target', 'away_deep', 
                     'away_ppda', 'home_draw_chances', 'home_loss_chances']
    
    # Add team power columns for home and away teams (based on goals, xG, etc.)
    df['home_team_power'] = df['home_goals'] + df['home_xg']  # You can adjust this as needed
    df['away_team_power'] = df['away_goals'] + df['away_xg']  # Similarly, adjust for away
    
    # Prepare home and away data
    home_data = df[df['team'] == df['home']]
    away_data = df[df['team'] == df['away']]
    
    # Calculate coefficients for home team power
    home_coefficients, home_intercept = calculate_coefficients(home_data, home_features, 'home_team_power')
    
    # Calculate coefficients for away team power
    away_coefficients, away_intercept = calculate_coefficients(away_data, away_features, 'away_team_power')
    
    # Print coefficients for home and away team powers
    print("Home Team Power Model Coefficients:")
    for feature, coef in zip(home_features, home_coefficients):
        print(f"{feature}: {coef}")
    print(f"Intercept: {home_intercept}")

    print("\nAway Team Power Model Coefficients:")
    for feature, coef in zip(away_features, away_coefficients):
        print(f"{feature}: {coef}")
    print(f"Intercept: {away_intercept}")

    # Example: Calculate team power for a given match
    example_home_stats = [27, 10, 13, 5.4444, 0.628, 0.2154]  # Example for Arsenal's home match
    example_away_stats = [6, 6, 2, 13.5455, 0.2154, 0.5531]  # Example for Leicester's away match
    
    home_power, away_power = calculate_team_power(example_home_stats, example_away_stats, 
                                                  home_coefficients, home_intercept,
                                                  away_coefficients, away_intercept)
    
    print("\nTeam Power Calculation for Example Match:")
    print(f"Home Team Power: {home_power}")
    print(f"Away Team Power: {away_power}")

if __name__ == "__main__":
    main()