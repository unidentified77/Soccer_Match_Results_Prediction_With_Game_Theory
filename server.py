from understatapi import UnderstatClient
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

# Initialize Understat API Client
understat = UnderstatClient()

# Define Player class
class Player:
    def __init__(
        self,
        player_name,
        avg_shots=0.0,
        avg_fouls=0.0,
        avg_yellow_cards=0.0,
        avg_red_cards=0.0,
        avg_passes_completed=0.0,
        avg_rating=0.0,
        position="",
        avg_xg=0.0,
    ):
        self.player_name = player_name
        self.avg_shots = avg_shots
        self.avg_fouls = avg_fouls
        self.avg_yellow_cards = avg_yellow_cards
        self.avg_red_cards = avg_red_cards
        self.avg_passes_completed = avg_passes_completed
        self.avg_rating = avg_rating
        self.position = position
        self.avg_xg = avg_xg

# Define Roster class
class Roster:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

# Define a base Team class
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

    # Fetch match data for a specific season
    def get_match_data(self, season, understat):
        try:
            return understat.team(team=self.name).get_match_data(season=season)
        except Exception as e:
            print(f"Error fetching match data for {self.name} in season {season}: {e}")
            return []

    # Fetch player data for a specific season
    def get_player_data(self, season, understat):
        try:
            return understat.team(team=self.name).get_player_data(season=season)
        except Exception as e:
            print(f"Error fetching player data for {self.name} in season {season}: {e}")
            return []

    # Extract player names from player data and fill roster
    def fill_roster_with_player_names(self, season, understat):
        player_data = self.get_player_data(season, understat)
        for player_info in player_data:
            player_name = player_info.get('player_name')
            if player_name:
                self.roster.add_player(Player(player_name=player_name))

# Define specific team classes
class Liverpool(Team):
    def __init__(self):
        super().__init__("Liverpool", "LIV")

class Chelsea(Team):
    def __init__(self):
        super().__init__("Chelsea", "CHE")

# Main function
def main():
    # Create team instances
    liverpool = Liverpool()
    chelsea = Chelsea()

    # Define seasons
    current_season = "2024"
    last_season = "2023"
    all_seasons = [str(year) for year in range(2017, 2024)]

    # Fetch all matches for Liverpool and Chelsea
    for team in [liverpool, chelsea]:
        for season in all_seasons:
            team.matches.extend(team.get_match_data(season, understat))

    # Fill averages for Liverpool
    fill_last_5_matches_avg_goals(liverpool)
    fill_this_season_avg_goals(liverpool, current_season, understat)
    fill_last_season_avg_goals(liverpool, last_season, understat)
    fill_total_avg_goals(liverpool)
    fill_last_5_matches_avg_xg(liverpool)
    fill_this_season_avg_xg(liverpool, current_season, understat)
    fill_last_season_avg_xg(liverpool, last_season, understat)
    fill_total_avg_xg(liverpool)

    # Fill averages for Chelsea
    fill_last_5_matches_avg_goals(chelsea)
    fill_this_season_avg_goals(chelsea, current_season, understat)
    fill_last_season_avg_goals(chelsea, last_season, understat)
    fill_total_avg_goals(chelsea)
    fill_last_5_matches_avg_xg(chelsea)
    fill_this_season_avg_xg(chelsea, current_season, understat)
    fill_last_season_avg_xg(chelsea, last_season, understat)
    fill_total_avg_xg(chelsea)

    # Print averages
    print(f"Liverpool's Averages:")
    print(f"Last 5 Matches Avg Goals: {liverpool.last_5_matches_avg_goals:.2f}")
    print(f"This Season Avg Goals: {liverpool.this_season_avg_goals:.2f}")
    print(f"Last Season Avg Goals: {liverpool.last_season_avg_goals:.2f}")
    print(f"Total Avg Goals: {liverpool.total_avg_goals:.2f}")
    print(f"Last 5 Matches Avg xG: {liverpool.last_5_matches_avg_xg:.2f}")
    print(f"This Season Avg xG: {liverpool.this_season_avg_xg:.2f}")
    print(f"Last Season Avg xG: {liverpool.last_season_avg_xg:.2f}")
    print(f"Total Avg xG: {liverpool.total_avg_xg:.2f}")

    print(f"\nChelsea's Averages:")
    print(f"Last 5 Matches Avg Goals: {chelsea.last_5_matches_avg_goals:.2f}")
    print(f"This Season Avg Goals: {chelsea.this_season_avg_goals:.2f}")
    print(f"Last Season Avg Goals: {chelsea.last_season_avg_goals:.2f}")
    print(f"Total Avg Goals: {chelsea.total_avg_goals:.2f}")
    print(f"Last 5 Matches Avg xG: {chelsea.last_5_matches_avg_xg:.2f}")
    print(f"This Season Avg xG: {chelsea.this_season_avg_xg:.2f}")
    print(f"Last Season Avg xG: {chelsea.last_season_avg_xg:.2f}")
    print(f"Total Avg xG: {chelsea.total_avg_xg:.2f}")

    # Fetch and print roster player names for Liverpool and Chelsea
    print("\nFetching rosters for Liverpool and Chelsea...")
    liverpool.fill_roster_with_player_names(current_season, understat)
    chelsea.fill_roster_with_player_names(current_season, understat)

    print("\nLiverpool Roster:")
    for player in liverpool.roster.players:
        print(player.player_name)

    print("\nChelsea Roster:")
    for player in chelsea.roster.players:
        print(player.player_name)
if __name__ == "__main__":
    main()
