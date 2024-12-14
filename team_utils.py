import numpy as np

def fill_last_5_matches_avg_goals(team):
    last_5_matches_goals = []
    for match in team.matches[-5:]:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                last_5_matches_goals.append(int(match['goals']['h']))
            elif match['a']['short_title'] == team.short_title:
                last_5_matches_goals.append(int(match['goals']['a']))

    team.last_5_matches_avg_goals = np.mean(last_5_matches_goals) if last_5_matches_goals else 0.0

def fill_this_season_avg_goals(team, season, understat):
    season_goals = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                season_goals.append(int(match['goals']['h']))
            elif match['a']['short_title'] == team.short_title:
                season_goals.append(int(match['goals']['a']))

    team.this_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

def fill_last_season_avg_goals(team, season, understat):
    season_goals = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                season_goals.append(int(match['goals']['h']))
            elif match['a']['short_title'] == team.short_title:
                season_goals.append(int(match['goals']['a']))

    team.last_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

def fill_total_avg_goals(team):
    total_goals = []
    for match in team.matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                total_goals.append(int(match['goals']['h']))
            elif match['a']['short_title'] == team.short_title:
                total_goals.append(int(match['goals']['a']))

    team.total_avg_goals = np.mean(total_goals) if total_goals else 0.0

# Similar functions for xG (Expected Goals)
def fill_last_5_matches_avg_xg(team):
    last_5_matches_xg = []
    for match in team.matches[-5:]:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                last_5_matches_xg.append(float(match['xG']['h']))
            elif match['a']['short_title'] == team.short_title:
                last_5_matches_xg.append(float(match['xG']['a']))

    team.last_5_matches_avg_xg = np.mean(last_5_matches_xg) if last_5_matches_xg else 0.0

def fill_this_season_avg_xg(team, season, understat):
    season_xg = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                season_xg.append(float(match['xG']['h']))
            elif match['a']['short_title'] == team.short_title:
                season_xg.append(float(match['xG']['a']))

    team.this_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

def fill_last_season_avg_xg(team, season, understat):
    season_xg = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                season_xg.append(float(match['xG']['h']))
            elif match['a']['short_title'] == team.short_title:
                season_xg.append(float(match['xG']['a']))

    team.last_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

def fill_total_avg_xg(team):
    total_xg = []
    for match in team.matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                total_xg.append(float(match['xG']['h']))
            elif match['a']['short_title'] == team.short_title:
                total_xg.append(float(match['xG']['a']))

    team.total_avg_xg = np.mean(total_xg) if total_xg else 0.0
