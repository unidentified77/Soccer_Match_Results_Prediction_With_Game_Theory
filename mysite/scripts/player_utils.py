
# player_utils.py

import numpy as np
from typing import Optional, Union

from utils import sd, pd, UnderstatClient, np

def fetch_match_players(match_id, understat: UnderstatClient):
    """Bir maç id'sine göre maçtaki oyuncu verilerini çeker."""
    try:
        return understat.match(match_id).get_roster_data()
    except Exception:
        return {}



def fill_last_5_matches_avg_goals_and_xg(team, understat: UnderstatClient):
    """Son 5 maçta oyuncuların ortalama gol ve xG istatistiklerini doldurur."""
    player_stats = {}
    for match in team.matches[-5:]:
        match_id = match['id']
        players = fetch_match_players(match_id, understat)
        if not players:
            continue
        for team_side in ['h', 'a']:
            team_players = players.get(team_side, {})
            for player_id, player_data in team_players.items():
                goals = int(player_data.get('goals', 0))
                xg = float(player_data.get('xG', 0.0))
                player_name = player_data.get('player', 'Unknown')
                if player_id not in player_stats:
                    player_stats[player_id] = {
                        'name': player_name,
                        'goals': [],
                        'xG': []
                    }
                player_stats[player_id]['goals'].append(goals)
                player_stats[player_id]['xG'].append(xg)
    team.last_5_matches_player_stats = {
        player_id: {
            'name': stats['name'],
            'avg_goals': np.mean(stats['goals']) if stats['goals'] else 0.0,
            'avg_xG': np.mean(stats['xG']) if stats['xG'] else 0.0
        }
        for player_id, stats in player_stats.items()
    }


def fill_season_avg_goals_and_xg(team, season: str, understat: UnderstatClient):
    """Verilen sezondaki oyuncuların ortalama gol ve xG istatistiklerini doldurur."""
    player_stats = {}
    matches = team.get_match_data(season, understat)
    for match in matches:
        match_id = match['id']
        players = fetch_match_players(match_id, understat)
        if not players:
            continue
        for team_side in ['h', 'a']:
            team_players = players.get(team_side, {})
            for player_id, player_data in team_players.items():
                goals = int(player_data.get('goals', 0))
                xg = float(player_data.get('xG', 0.0))
                player_name = player_data.get('player', 'Unknown')
                if player_id not in player_stats:
                    player_stats[player_id] = {
                        'name': player_name,
                        'goals': [],
                        'xG': []
                    }
                player_stats[player_id]['goals'].append(goals)
                player_stats[player_id]['xG'].append(xg)
    team.season_player_stats = {
        player_id: {
            'name': stats['name'],
            'avg_goals': np.mean(stats['goals']) if stats['goals'] else 0.0,
            'avg_xG': np.mean(stats['xG']) if stats['xG'] else 0.0
        }
        for player_id, stats in player_stats.items()
    }


def fill_total_avg_goals_and_xg(team, understat: UnderstatClient):
    """Takımın tüm maçlarındaki oyuncuların ortalama gol ve xG istatistiklerini hesaplar."""
    player_stats = {}
    for match in team.matches:
        match_id = match['id']
        players = fetch_match_players(match_id, understat)
        if not players:
            continue
        for team_side in ['h', 'a']:
            team_players = players.get(team_side, {})
            for player_id, player_data in team_players.items():
                goals = int(player_data.get('goals', 0))
                xg = float(player_data.get('xG', 0.0))
                player_name = player_data.get('player', 'Unknown')
                if player_id not in player_stats:
                    player_stats[player_id] = {
                        'name': player_name,
                        'goals': [],
                        'xG': []
                    }
                player_stats[player_id]['goals'].append(goals)
                player_stats[player_id]['xG'].append(xg)
    team.total_player_stats = {
        player_id: {
            'name': stats['name'],
            'avg_goals': np.mean(stats['goals']) if stats['goals'] else 0.0,
            'avg_xG': np.mean(stats['xG']) if stats['xG'] else 0.0
        }
        for player_id, stats in player_stats.items()
    }


def get_passing_accuracy(team_name: str, season: Union[str, int]) -> Optional[float]:
    """Takımın passing accuracy yüzdesini FBref üzerinden döndürür."""
    try:
        fbref = sd.FBref(leagues=['ENG-Premier League'], seasons=[season])
        passing_stats = fbref.read_team_season_stats(stat_type='passing')
        if passing_stats.empty:
            return None
        passing_stats = passing_stats.reset_index()

        # Çoklu kolon isimlendirmesi düzeltme
        if isinstance(passing_stats.columns, pd.MultiIndex):
            passing_stats.columns = [
                '_'.join(col).strip() if col[1] else col[0]
                for col in passing_stats.columns
            ]
        team_data = passing_stats[passing_stats['team'] == team_name]
        if team_data.empty:
            return None
        if 'Total_Cmp' not in team_data.columns or 'Total_Att' not in team_data.columns:
            return None

        total_cmp = team_data['Total_Cmp'].sum()
        total_att = team_data['Total_Att'].sum()
        if total_att == 0:
            return None
        total_pass_accuracy = (total_cmp / total_att) * 100
        return float(total_pass_accuracy)
    except:
        return None


def get_shots_on_target(team_name: str, season: Union[str, int]) -> Optional[float]:
    """Takımın toplam 'Shots on Target' (SoT) değerini FBref üzerinden bulur."""
    try:
        fbref = sd.FBref(leagues=['ENG-Premier League'], seasons=[season])
        shooting_stats = fbref.read_team_season_stats(stat_type='shooting')
        if shooting_stats.empty:
            return None
        shooting_stats = shooting_stats.reset_index()

        if isinstance(shooting_stats.columns, pd.MultiIndex):
            shooting_stats.columns = [
                '_'.join(col).strip() if col[1] else col[0]
                for col in shooting_stats.columns
            ]
        team_data = shooting_stats[shooting_stats['team'] == team_name]
        if team_data.empty:
            return None

        sot_col = next((c for c in team_data.columns if 'SoT' in c), None)
        if sot_col is None:
            return None
        shots_on_target = team_data[sot_col].sum()
        return float(shots_on_target)
    except:
        return None


def get_possession_percentage(team_name: str, season: Union[str, int]) -> Optional[float]:
    """Takımın ortalama topa sahip olma yüzdesini FBref üzerinden bulur."""
    try:
        fbref = sd.FBref(leagues=['ENG-Premier League'], seasons=[season])
        possession_stats = fbref.read_team_season_stats(stat_type='possession')
        if possession_stats.empty:
            return None
        possession_stats = possession_stats.reset_index()

        if isinstance(possession_stats.columns, pd.MultiIndex):
            possession_stats.columns = [
                '_'.join(col).strip() if col[1] else col[0]
                for col in possession_stats.columns
            ]
        team_data = possession_stats[possession_stats['team'] == team_name]
        if team_data.empty:
            return None

        poss_col = next((c for c in team_data.columns if c.endswith('Poss')), None)
        if poss_col is None:
            return None
        possession = team_data[poss_col].mean()
        return float(possession)
    except:
        return None


def get_total_shots(team_name: str, season: Union[str, int]) -> Optional[int]:
    """Takımın toplam şut sayısını FBref üzerinden döndürür."""
    try:
        fbref = sd.FBref(leagues=['ENG-Premier League'], seasons=[season])
        shooting_stats = fbref.read_team_season_stats(stat_type='shooting')
        if shooting_stats.empty:
            return None
        shooting_stats = shooting_stats.reset_index()

        if isinstance(shooting_stats.columns, pd.MultiIndex):
            shooting_stats.columns = [
                '_'.join(col).strip() if col[1] else col[0]
                for col in shooting_stats.columns
            ]
        team_data = shooting_stats[shooting_stats['team'] == team_name]
        if team_data.empty:
            return None

        shots_col = next((c for c in team_data.columns if c.lower() == 'sh'), None)
        if shots_col is None:
            shots_col = next((c for c in team_data.columns if 'sh' in c.lower()), None)
        if shots_col is None:
            return None

        total_shots = team_data[shots_col].sum()
        return int(total_shots)
    except:
        return None

def get_last_match_id_from_schedule(team_name: str, season: Union[str,int]) -> Optional[str]:
    """Takımın sezondaki son maçının 'game_id' değerini FBref'ten alır."""
    try:
        fbref = sd.FBref(leagues="ENG-Premier League", seasons=[season])
        schedule = fbref.read_schedule()
        if schedule.empty:
            return None
        team_col_home = next((col for col in schedule.columns if 'home_team' in col.lower()), None)
        team_col_away = next((col for col in schedule.columns if 'away_team' in col.lower()), None)
        date_col = next((col for col in schedule.columns if 'date' in col.lower()), None)
        game_id_col = 'game_id' if 'game_id' in schedule.columns else None
        if not team_col_home or not team_col_away or not date_col or not game_id_col:
            return None

        team_matches = schedule[(schedule[team_col_home] == team_name) | (schedule[team_col_away] == team_name)]
        if team_matches.empty:
            return None
        completed_matches = team_matches[team_matches[game_id_col].notna()]
        if completed_matches.empty:
            return None
        completed_matches = completed_matches.sort_values(by=date_col)
        last_match = completed_matches.iloc[-1]
        game_id_val = last_match[game_id_col]
        if pd.isna(game_id_val):
            return None
        game_id_str = str(game_id_val).strip()
        if not game_id_str or game_id_str.lower() == 'nan':
            return None
        return game_id_str
    except:
        return None
    
def get_last_match_formation(team_name: str, season: Union[str, int]) -> Optional[str]:
    """FBref'teki 'schedule' tablosundaki 'Formation' bilgisinden son maç formasyonu döndürür."""
    try:
        fbref = sd.FBref(leagues="ENG-Premier League", seasons=[season])
        team_match_stats = fbref.read_team_match_stats(stat_type="schedule", team=team_name)
        if team_match_stats.empty:
            return None
        date_column = next((col for col in team_match_stats.columns if 'date' in col.lower()), None)
        if date_column:
            team_match_stats = team_match_stats.sort_values(by=date_column)
            last_match = team_match_stats.iloc[-1]
            formation_val = last_match.get('Formation', None)
            # Eğer Pandas NA ise None dönelim:
            if pd.isna(formation_val):
                return None
            return str(formation_val)
        return None
    except:
        return None




def get_starting_eleven(team_name: str, season: Union[str,int]) -> Optional[list]:
    """Takımın son maçındaki ilk 11 (oyuncu, mevki) listesini döndürür."""
    match_id = get_last_match_id_from_schedule(team_name, season)
    if not match_id:
        return None
    try:
        fbref = sd.FBref(leagues="ENG-Premier League", seasons=[season])
        lineups = fbref.read_lineup(match_id=match_id)
        if lineups.empty:
            return None
        team_lineup = lineups[(lineups['team'] == team_name) & (lineups['is_starter'] == True)]
        if team_lineup.empty:
            return None
        return list(zip(team_lineup['player'], team_lineup['position']))
    except:
        return None


def classify_position(pos_str: str) -> str:
    """Mevkileri basitçe F, D, M şeklinde gruplar."""
    pos_upper = pos_str.upper()
    forwards = ['FW', 'LW', 'RW']
    defenders = ['CB', 'LB', 'RB', 'WB']
    midfield = ['DM', 'CM', 'AM', 'RM', 'LM']

    if any(f in pos_upper for f in forwards):
        return 'F'
    if any(d in pos_upper for d in defenders):
        return 'D'
    if any(m in pos_upper for m in midfield):
        return 'M'
    return 'M'

def guess_formation_from_lineup(lineup: list) -> str:
    """
    İlk 11'den yola çıkarak basit formasyon tahmini.
    Burada 4-2-3-1 gibi daha fazla varyasyon ekledik.
    """
    field_positions = []
    for player, pos in lineup:
        # Kaleci GK'i atlıyoruz
        if 'GK' in pos.upper():
            continue

        sub_positions = [p.strip() for p in pos.split(',')]
        best_rank = 99
        best_label = 'M'
        for sp in sub_positions:
            label = classify_position(sp)
            # F=1, D=2, M=3 => forvet daha kritik vs. diye
            rank = {'F':1,'D':2,'M':3}.get(label, 3)
            if rank < best_rank:
                best_rank = rank
                best_label = label
        field_positions.append(best_label)

    if len(field_positions) != 10:
        return "Unknown Formation"

    d_count = field_positions.count('D')
    m_count = field_positions.count('M')
    f_count = field_positions.count('F')

    known_formations = {
        (4, 3, 3): "4-3-3",
        (4, 4, 2): "4-4-2",
        (4, 5, 1): "4-5-1",
        (3, 5, 2): "3-5-2",
        (5, 3, 2): "5-3-2",
        (3, 4, 3): "3-4-3",
        (4, 5, 1): "4-2-3-1",  # Önemli: 4-2-3-1 eklendi
        (5, 4, 1): "5-4-1",
        (3, 6, 1): "3-6-1",
    }

    if (d_count, m_count, f_count) in known_formations:
        return known_formations[(d_count, m_count, f_count)]

    return f"{d_count}-{m_count}-{f_count}"