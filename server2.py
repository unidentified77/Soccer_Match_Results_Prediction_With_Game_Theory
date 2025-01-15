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
        self.avg_shots = None
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

    def get_top_scorers(self):
        """Get top players based on goals and xG."""
        return sorted(self.roster, key=lambda p: p.get_player_strength(), reverse=True)


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


def main():
    liverpool = Team("Liverpool", "LIV")
    chelsea = Team("Chelsea", "CHE")

    current_season = "2024"
    last_season = "2023"
    all_seasons = [str(year) for year in range(2017, 2024)]

    for t in [liverpool, chelsea]:
        # Gather all data
        for season in all_seasons:
            t.matches.extend(t.get_match_data(season, understat))

        fill_last_5_matches_avg_goals(t)
        fill_this_season_avg_goals(t, current_season, understat)
        fill_last_season_avg_goals(t, last_season, understat)
        fill_total_avg_goals(t)
        fill_last_5_matches_avg_xg(t)
        fill_this_season_avg_xg(t, current_season, understat)
        fill_last_season_avg_xg(t, last_season, understat)
        fill_total_avg_xg(t)

        fill_last_5_matches_gk_stats(t)
        fill_this_season_gk_stats(t, current_season, understat)
        fill_last_season_gk_stats(t, last_season, understat)
        fill_total_gk_stats(t)

        fill_last_5_matches_avg_goals_and_xg(t, understat)
        fill_season_avg_goals_and_xg(t, current_season, understat)
        fill_total_avg_goals_and_xg(t, understat)

        t.fill_roster_with_player_data(current_season, understat)

        t.possession_percentage = get_possession_percentage(t.name, current_season)
        t.passing_accuracy = get_passing_accuracy(t.name, current_season)
        t.shots_on_target = get_shots_on_target(t.name, current_season)
        t.total_shots = get_total_shots(t.name, current_season)

    # Get starting elevens
    liverpool_xi = get_starting_eleven("Liverpool", current_season)
    chelsea_xi = get_starting_eleven("Chelsea", current_season)

    liverpool_formation_from_xi = guess_formation_from_lineup(liverpool_xi) if liverpool_xi else 'Unknown Formation'
    chelsea_formation_from_xi = guess_formation_from_lineup(chelsea_xi) if chelsea_xi else 'Unknown Formation'


    liv_form = get_last_match_formation("Liverpool", current_season)
    che_form = get_last_match_formation("Chelsea", current_season)

    liv_form = safe_convert_formation(liv_form)
    che_form = safe_convert_formation(che_form)

    if liv_form is None:
        liv_form = liverpool_formation_from_xi
        liverpool.formation = liverpool_formation_from_xi
    if che_form is None:
        che_form = chelsea_formation_from_xi
        chelsea.formation = chelsea_formation_from_xi

    liverpool.last_match_formation = liv_form
    chelsea.last_match_formation = che_form

    # Determine formation and play style
    liverpool_formation = determine_team_formation(liverpool)
    liverpool_style = determine_team_play_style(liverpool)
    liverpool.style = liverpool_style

    chelsea_formation = determine_team_formation(chelsea)
    chelsea_style = determine_team_play_style(chelsea)
    chelsea.style = chelsea_style

    # Print all data we have before making the prediction
    def print_team_data(team):
        print(f"Team: {team.name}")
        print(f"Last 5 Matches Avg Goals: {team.last_5_matches_avg_goals}")
        print(f"This Season Avg Goals: {team.this_season_avg_goals}")
        print(f"Last Season Avg Goals: {team.last_season_avg_goals}")
        print(f"Total Avg Goals: {team.total_avg_goals}")
        print(f"Last 5 Matches Avg xG: {team.last_5_matches_avg_xg}")
        print(f"This Season Avg xG: {team.this_season_avg_xg}")
        print(f"Last Season Avg xG: {team.last_season_avg_xg}")
        print(f"Total Avg xG: {team.total_avg_xg}")
        print(f"Formation (Last Match/From XI): {team.last_match_formation}")
        print(f"Possession: {team.possession_percentage}")
        print(f"Passing Accuracy: {team.passing_accuracy}")
        print(f"Shots on Target: {team.shots_on_target}")
        print(f"Total Shots: {team.total_shots}")
        print(f"Determined Formation: {determine_team_formation(team)}")
        print(f"Determined Play Style: {determine_team_play_style(team)}")
        print("Top Players by avg_goals and avg_xg:")
        # Sort players by (avg_goals*0.7 + avg_xg*0.3)
        scored_players = [(p.avg_goals*0.7+p.avg_xg*0.3, p.player_name, p.avg_goals, p.avg_xg) for p in team.roster.players]
        scored_players.sort(reverse=True, key=lambda x:x[0])
        for sp in scored_players[:10]:
            print(f"Player: {sp[1]}, score_metric: {sp[0]:.2f}, avg_goals: {sp[2]:.2f}, avg_xg: {sp[3]:.2f}")
        print("----")

    print("=== DATA FOR LIVERPOOL ===")
    print_team_data(liverpool)
    print("=== DATA FOR CHELSEA ===")
    print_team_data(chelsea)

    print("=== STARTING ELEVENS ===")
    if liverpool_xi:
        print("Liverpool XI:")
        for p, pos in liverpool_xi:
            print(f"{p} - {pos}")
    else:
        print("No XI data for Liverpool")

    if chelsea_xi:
        print("Chelsea XI:")
        for p, pos in chelsea_xi:
            print(f"{p} - {pos}")
    else:
        print("No XI data for Chelsea")

    def team_strength(team):
        strength = (team.total_avg_goals + team.total_avg_xg) / 2
        if team.passing_accuracy: strength += (team.passing_accuracy / 100) * 0.5
        if team.possession_percentage: strength += (team.possession_percentage / 100) * 0.5
        if team.shots_on_target: strength += (team.shots_on_target / 10)
        if team.total_shots: strength += (team.total_shots / 50)
        return strength

    liv_strength = team_strength(liverpool)
    che_strength = team_strength(chelsea)

    def parse_formation_string(formation_str):
        parts = formation_str.split('-')
        try:
            d = int(parts[0])
            m = int(parts[1])
            f = int(parts[2])
            return d,m,f
        except:
            return 4,4,2

    l_d,l_m,l_f = parse_formation_string(liverpool_formation_from_xi) if liverpool_formation_from_xi != 'Unknown Formation' else (4,4,2)
    c_d,c_m,c_f = parse_formation_string(chelsea_formation_from_xi) if chelsea_formation_from_xi != 'Unknown Formation' else (4,4,2)

    if l_f > c_d: liv_strength += 1.0
    if c_f > l_d: che_strength += 1.0

    if liverpool_style == "High Press" and chelsea_style == "Low Press":
        liv_strength += 1
    if chelsea_style == "High Press" and liverpool_style == "Low Press":
        che_strength += 1

    if liverpool_style == "Possession Based" and chelsea_style == "Counter Attack":
        liv_strength += 0.5
    if chelsea_style == "Possession Based" and liverpool_style == "Counter Attack":
        che_strength += 0.5

    diff = liv_strength - che_strength

    avg_goals_factor = (liverpool.last_5_matches_avg_goals + chelsea.last_5_matches_avg_goals) / 2
    avg_goals_factor = max(avg_goals_factor, 1.0)

    liv_goals = avg_goals_factor + (diff * 0.5)
    che_goals = avg_goals_factor - (diff * 0.5)
    liv_goals = max(liv_goals,0)
    che_goals = max(che_goals,0)
    liv_goals_int = int(round(liv_goals))
    che_goals_int = int(round(che_goals))

    def top_scorers(team):
        scoring_list = []
        for p in team.roster.players:
            score_metric = p.avg_goals*0.7 + p.avg_xg*0.3
            scoring_list.append((score_metric, p.player_name))
        scoring_list.sort(reverse=True,key=lambda x:x[0])
        return [name for _, name in scoring_list]

    liv_scorers = top_scorers(liverpool)
    che_scorers = top_scorers(chelsea)

    def assign_scorers(goals, scorer_candidates):
        if goals <= 0:
            return []
        return scorer_candidates[:goals] if len(scorer_candidates) >= goals else scorer_candidates

    liv_goal_scorers = assign_scorers(liv_goals_int, liv_scorers)
    che_goal_scorers = assign_scorers(che_goals_int, che_scorers)

    # Print final prediction
    print("\n=== PREDICTION RESULT ===")
    print(f"Predicted Match Result: {liverpool.name} {liv_goals_int}-{che_goals_int} {chelsea.name}")
    print(f"{liverpool.name} Formation: {liverpool_formation}, Style: {liverpool_style}")
    print(f"{chelsea.name} Formation: {chelsea_formation}, Style: {chelsea_style}")

    if liv_goal_scorers:
        print(f"{liverpool.name} Goals by: {', '.join(liv_goal_scorers)}")
    if che_goal_scorers:
        print(f"{chelsea.name} Goals by: {', '.join(che_goal_scorers)}")

    print("\nReasoning:")
    print("- Used historical averages (goals, xG) and passing/shooting data to estimate base strength.")
    print("- Adjusted strengths for formation and style matchups (e.g. High Press vs Low Press).")
    print("- Converted strength differences into a scoreline influenced by avg_goals_factor.")
    print("- Selected goalscorers based on a metric combining avg_goals and avg_xg.")
    print("- All data from rosters, averages, formations, and styles has been utilized in the logic.")

########################################################################################################################
#                                                                                                                      #
#             HOME TEAM AND AWAY TEAM POWER CALCULATION BY CALCULATING COEFFICIENTS WITH LINEAR REGRESSION             #
#                                                                                                                      #
########################################################################################################################


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


    # Example: Calculate team power for a given match ----- To fill this first run calculate_team_features_for_team_power.py, dont forget to change the teams
    #home_shots, home_shots_on_target, home_deep, home_ppda, home_win_chances, home_draw_chances]
    example_home_stats = [16.2, 6.8, 10.8, 9.7, 0.68, 0.18]  # Example for Arsenal's home match
    # away_shots, away_shots_on_target, away_deep, away_ppda, home_draw_chances, home_loss_chances
    example_away_stats = [15, 5.4, 11, 9.8, 0.2, 0.44]  # Example for Leicester's away match
    
    home_power, away_power = calculate_team_power(example_home_stats, example_away_stats, 
                                                  home_coefficients, home_intercept,
                                                  away_coefficients, away_intercept)
    
    print("\nTeam Power Calculation for Example Match:")
    print(f"Home Team Power: {home_power}")
    print(f"Away Team Power: {away_power}")
    print("chelsea.total_shots")
    print(chelsea.total_shots)
    print(chelsea.avg_shots)
########################################################################################################################
#                                                                                                                      #
#             HOME TEAM AND AWAY TEAM POWER CALCULATION BY CALCULATING COEFFICIENTS WITH LINEAR REGRESSION             #
#                                                                                                                      #
########################################################################################################################
    
    #liverpool_goals, chelsea_goals = game_theory_prediction(liverpool, chelsea)

    #print(f"Predicted Score: {liverpool.name} {liverpool_goals}-{chelsea_goals} {chelsea.name}")


if __name__ == "__main__":
    main()
