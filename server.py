from understatapi import UnderstatClient
import numpy as np

# Initialize Understat API Client
understat = UnderstatClient()

# Global mapping for short titles
short_title_map = {
    "Liverpool": "LIV",
    "Chelsea": "CHE"
}

# Function to fetch matches between two teams across multiple seasons
def get_team_matches_across_seasons(team1, team2, seasons):
    matches = []
    for season in seasons:
        # Fetch matches for the current season
        season_matches = get_team_matches(team1, team2, season=season)
        matches.extend(season_matches)
    return matches

# Function to fetch matches between two teams in a season
def get_team_matches(team1, team2, season="2023"):
    # Fetch all matches for both teams
    team1_matches = understat.team(team=team1).get_match_data(season=season)
    team2_matches = understat.team(team=team2).get_match_data(season=season)

    # Normalize short titles
    team1_short = short_title_map.get(team1, team1)
    team2_short = short_title_map.get(team2, team2)

    # Filter matches where both teams played against each other
    matches = []
    for match in team1_matches:
        if (match['h']['short_title'] == team1_short and match['a']['short_title'] == team2_short) or \
           (match['h']['short_title'] == team2_short and match['a']['short_title'] == team1_short):
            matches.append(match)

    return matches

# Main script to analyze matches and predict outcomes
def main():
    # Define the teams
    team1 = "Liverpool"
    team2 = "Chelsea"
    seasons = [str(year) for year in range(2017, 2024)]  # Seasons from 2017 to 2023

    # Fetch matches across all seasons
    matches = get_team_matches_across_seasons(team1, team2, seasons)
    print(f"Matches between {team1} and {team2}: {matches}")

    if not matches:
        print("No valid match data found between the teams.")
        return

    # Initialize lists to store goals and xG data
    team1_goals = []
    team2_goals = []
    team1_xg = []
    team2_xg = []

    # Extract data for goals and xG
    for match in matches:
        if 'goals' in match and 'xG' in match:
            if match['h']['short_title'] == short_title_map[team1]:  # team1 as home
                team1_goals.append(int(match['goals']['h']))
                team2_goals.append(int(match['goals']['a']))
                team1_xg.append(float(match['xG']['h']))
                team2_xg.append(float(match['xG']['a']))
            elif match['a']['short_title'] == short_title_map[team1]:  # team1 as away
                team1_goals.append(int(match['goals']['a']))
                team2_goals.append(int(match['goals']['h']))
                team1_xg.append(float(match['xG']['a']))
                team2_xg.append(float(match['xG']['h']))

    # Calculate the average goals and xG for each team
    if team1_goals and team2_goals:
        avg_team1_goals = np.mean(team1_goals)
        avg_team2_goals = np.mean(team2_goals)
        avg_team1_xg = np.mean(team1_xg)
        avg_team2_xg = np.mean(team2_xg)

        # Print the average goals and xG
        print(f"Average Goals Scored by {team1}: {avg_team1_goals:.2f}")
        print(f"Average Goals Scored by {team2}: {avg_team2_goals:.2f}")
        print(f"Average xG for {team1}: {avg_team1_xg:.2f}")
        print(f"Average xG for {team2}: {avg_team2_xg:.2f}")

        # Simple Prediction Logic based on Goals
        if avg_team1_goals > avg_team2_goals:
            prediction = f"{team1} is more likely to win"
        elif avg_team1_goals < avg_team2_goals:
            prediction = f"{team2} is more likely to win"
        else:
            prediction = "The match is likely to be a draw"

        print(f"Prediction: {prediction}")
    else:
        print("Not enough data to calculate averages or predict outcomes.")

# Run the script
if __name__ == "__main__":
    main()
