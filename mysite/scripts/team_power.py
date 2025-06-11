
# team_power.py

from utils import pd, np, UnderstatClient
from team_utils import (
    fill_last_5_matches_avg_goals, fill_this_season_avg_goals, fill_last_season_avg_goals,
    fill_total_avg_goals,
    fill_last_5_matches_avg_xg, fill_this_season_avg_xg, fill_last_season_avg_xg, fill_total_avg_xg
)
from player_utils import (
    get_last_match_formation,
    get_starting_eleven,
    guess_formation_from_lineup,
    get_possession_percentage,
    get_passing_accuracy,
    get_shots_on_target,
    get_total_shots
)

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
        """Basit örnek: Gol ve xG üzerinden."""
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

        # Gol ortalamaları
        self.last_5_matches_avg_goals = 0.0
        self.this_season_avg_goals = 0.0
        self.last_season_avg_goals = 0.0
        self.total_avg_goals = 0.0

        # xG ortalamaları
        self.last_5_matches_avg_xg = 0.0
        self.this_season_avg_xg = 0.0
        self.last_season_avg_xg = 0.0
        self.total_avg_xg = 0.0

        # Tüm maç verileri
        self.matches = []
        self.roster = Roster()

        # FBref metrikleri
        self.possession_percentage = None
        self.passing_accuracy = None
        self.shots_on_target = None
        self.total_shots = None

        self.last_match_formation = None
        self.formation = None
        self.style = None

    def get_match_data(self, season, understat: UnderstatClient):
        try:
            return understat.team(team=self.name).get_match_data(season=season)
        except:
            return []

    def get_player_data(self, season, understat: UnderstatClient):
        try:
            return understat.team(team=self.name).get_player_data(season=season)
        except:
            return []

    def fill_roster_with_player_data(self, season, understat: UnderstatClient):
        data = self.get_player_data(season, understat)
        for p in data:
            pname = p.get('player_name')
            pid = p.get('id')
            g = float(p.get('goals', 0))
            gm = float(p.get('games', 0))
            avg_g = g / gm if gm > 0 else 0.0
            avg_x = float(p.get('xG', 0)) / gm if gm > 0 else 0.0
            avg_sh = float(p.get('shots', 0)) / gm if gm > 0 else 0.0
            avg_yc = float(p.get('yellow_cards', 0)) / gm if gm > 0 else 0.0
            avg_rc = float(p.get('red_cards', 0)) / gm if gm > 0 else 0.0
            pos = p.get('position', "")
            if pname and pid:
                self.roster.add_player(Player(
                    player_name=pname,
                    player_id=pid,
                    avg_goals=avg_g,
                    avg_xg=avg_x,
                    avg_shots=avg_sh,
                    avg_yellow_cards=avg_yc,
                    avg_red_cards=avg_rc,
                    position=pos
                ))

    def calculate_team_strength(self):
        """
        Daha kompleks bir hesap:
          1) Average Goals & xG
          2) Passing & Possession
          3) Shots on Target & total Shots
          4) (Defans kalitesi – currently omitted)
          5) Roster kalitesi ortalaması (örnek)
        Her birine bir ağırlık verebilirsiniz.
        """
        base = 0.0

        # 1) Gol & xG
        attack_factor = (self.total_avg_goals + self.total_avg_xg) / 2.0
        base += attack_factor

        # 2) Pas + topa sahip olma
        if self.passing_accuracy:
            base += (self.passing_accuracy / 100) * 0.5
        if self.possession_percentage:
            base += (self.possession_percentage / 100) * 0.5

        # 3) Şut verileri
        if self.shots_on_target:
            base += (self.shots_on_target / 10)
        if self.total_shots:
            base += (self.total_shots / 50)

        # 5) Roster ortalama gücü
        roster_strength = 0.0
        if self.roster.players:
            ssum = sum(pl.get_player_strength() for pl in self.roster.players)
            roster_strength = ssum / len(self.roster.players)
        base += roster_strength * 0.5  # Örneğin 0.5 weighting

        return base


def fill_all_stats(team: Team, current_season: str, last_season: str, all_seasons: list, understat: UnderstatClient):
    """Takımdaki tüm verileri doldurur."""
    # Tüm sezonların maçlarını ekle
    for s in all_seasons:
        team.matches.extend(team.get_match_data(s, understat))

    # Gol & xG
    fill_last_5_matches_avg_goals(team)
    fill_this_season_avg_goals(team, current_season, understat)
    fill_last_season_avg_goals(team, last_season, understat)
    fill_total_avg_goals(team)

    fill_last_5_matches_avg_xg(team)
    fill_this_season_avg_xg(team, current_season, understat)
    fill_last_season_avg_xg(team, last_season, understat)
    fill_total_avg_xg(team)

    # GK stats removed

    # Roster
    team.fill_roster_with_player_data(current_season, understat)

    # FBref metrikler
    team.possession_percentage = get_possession_percentage(team.name, current_season)
    team.passing_accuracy = get_passing_accuracy(team.name, current_season)
    team.shots_on_target = get_shots_on_target(team.name, current_season)
    team.total_shots = get_total_shots(team.name, current_season)

    # Son maç formasyonu
    lm_form = get_last_match_formation(team.name, current_season)
    if lm_form is None or pd.isna(lm_form):
        lineup = get_starting_eleven(team.name, current_season)
        if lineup:
            lm_form = guess_formation_from_lineup(lineup)

    team.last_match_formation = lm_form if lm_form else "Unknown Formation"