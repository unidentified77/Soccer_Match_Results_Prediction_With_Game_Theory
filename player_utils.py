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