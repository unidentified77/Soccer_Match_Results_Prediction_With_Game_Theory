from understatapi import UnderstatClient
import numpy as np

# Initialize Understat API Client
understat = UnderstatClient()

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

    # Fetch match data for a specific season
    def get_match_data(self, season):
        try:
            return understat.team(team=self.name).get_match_data(season=season)
        except Exception as e:
            print(f"Error fetching match data for {self.name} in season {season}: {e}")
            return []

    # Fill last 5 matches average goals
    def fill_last_5_matches_avg_goals(self):
        last_5_matches_goals = []
        for match in self.matches[-5:]:
            if 'goals' in match:
                if match['h']['short_title'] == self.short_title:
                    last_5_matches_goals.append(int(match['goals']['h']))
                elif match['a']['short_title'] == self.short_title:
                    last_5_matches_goals.append(int(match['goals']['a']))

        self.last_5_matches_avg_goals = np.mean(last_5_matches_goals) if last_5_matches_goals else 0.0

    # Fill this season average goals
    def fill_this_season_avg_goals(self, season):
        season_goals = []
        matches = self.get_match_data(season)
        for match in matches:
            if 'goals' in match:
                if match['h']['short_title'] == self.short_title:
                    season_goals.append(int(match['goals']['h']))
                elif match['a']['short_title'] == self.short_title:
                    season_goals.append(int(match['goals']['a']))

        self.this_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

    # Fill last season average goals
    def fill_last_season_avg_goals(self, season):
        season_goals = []
        matches = self.get_match_data(season)
        for match in matches:
            if 'goals' in match:
                if match['h']['short_title'] == self.short_title:
                    season_goals.append(int(match['goals']['h']))
                elif match['a']['short_title'] == self.short_title:
                    season_goals.append(int(match['goals']['a']))

        self.last_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

    # Fill total average goals across all available matches
    def fill_total_avg_goals(self):
        total_goals = []
        for match in self.matches:
            if 'goals' in match:
                if match['h']['short_title'] == self.short_title:
                    total_goals.append(int(match['goals']['h']))
                elif match['a']['short_title'] == self.short_title:
                    total_goals.append(int(match['goals']['a']))

        self.total_avg_goals = np.mean(total_goals) if total_goals else 0.0

    # Fill last 5 matches average xG
    def fill_last_5_matches_avg_xg(self):
        last_5_matches_xg = []
        for match in self.matches[-5:]:
            if 'xG' in match:
                if match['h']['short_title'] == self.short_title:
                    last_5_matches_xg.append(float(match['xG']['h']))
                elif match['a']['short_title'] == self.short_title:
                    last_5_matches_xg.append(float(match['xG']['a']))

        self.last_5_matches_avg_xg = np.mean(last_5_matches_xg) if last_5_matches_xg else 0.0

    # Fill this season average xG
    def fill_this_season_avg_xg(self, season):
        season_xg = []
        matches = self.get_match_data(season)
        for match in matches:
            if 'xG' in match:
                if match['h']['short_title'] == self.short_title:
                    season_xg.append(float(match['xG']['h']))
                elif match['a']['short_title'] == self.short_title:
                    season_xg.append(float(match['xG']['a']))

        self.this_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

    # Fill last season average xG
    def fill_last_season_avg_xg(self, season):
        season_xg = []
        matches = self.get_match_data(season)
        for match in matches:
            if 'xG' in match:
                if match['h']['short_title'] == self.short_title:
                    season_xg.append(float(match['xG']['h']))
                elif match['a']['short_title'] == self.short_title:
                    season_xg.append(float(match['xG']['a']))

        self.last_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

    # Fill total average xG across all available matches
    def fill_total_avg_xg(self):
        total_xg = []
        for match in self.matches:
            if 'xG' in match:
                if match['h']['short_title'] == self.short_title:
                    total_xg.append(float(match['xG']['h']))
                elif match['a']['short_title'] == self.short_title:
                    total_xg.append(float(match['xG']['a']))

        self.total_avg_xg = np.mean(total_xg) if total_xg else 0.0

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
    current_season = "2023"
    last_season = "2022"
    all_seasons = [str(year) for year in range(2017, 2024)]

    # Fetch all matches for Liverpool and Chelsea
    for team in [liverpool, chelsea]:
        for season in all_seasons:
            team.matches.extend(team.get_match_data(season))

    # Fill averages for Liverpool
    liverpool.fill_last_5_matches_avg_goals()
    liverpool.fill_this_season_avg_goals(current_season)
    liverpool.fill_last_season_avg_goals(last_season)
    liverpool.fill_total_avg_goals()
    liverpool.fill_last_5_matches_avg_xg()
    liverpool.fill_this_season_avg_xg(current_season)
    liverpool.fill_last_season_avg_xg(last_season)
    liverpool.fill_total_avg_xg()

    # Fill averages for Chelsea
    chelsea.fill_last_5_matches_avg_goals()
    chelsea.fill_this_season_avg_goals(current_season)
    chelsea.fill_last_season_avg_goals(last_season)
    chelsea.fill_total_avg_goals()
    chelsea.fill_last_5_matches_avg_xg()
    chelsea.fill_this_season_avg_xg(current_season)
    chelsea.fill_last_season_avg_xg(last_season)
    chelsea.fill_total_avg_xg()

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

if __name__ == "__main__":
    main()
