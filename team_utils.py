# team_utils.py
import numpy as np
from understatapi import UnderstatClient

def fill_last_5_matches_avg_goals(team):
    last_5_matches_goals = []
    for match in team.matches[-5:]:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                home_goals = match['goals'].get('h')
                if home_goals is not None:
                    last_5_matches_goals.append(int(home_goals))
            elif match['a']['short_title'] == team.short_title:
                away_goals = match['goals'].get('a')
                if away_goals is not None:
                    last_5_matches_goals.append(int(away_goals))
    team.last_5_matches_avg_goals = np.mean(last_5_matches_goals) if last_5_matches_goals else 0.0

def fill_this_season_avg_goals(team, season, understat):
    season_goals = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                home_goals = match['goals'].get('h')
                if home_goals is not None:
                    season_goals.append(int(home_goals))
            elif match['a']['short_title'] == team.short_title:
                away_goals = match['goals'].get('a')
                if away_goals is not None:
                    season_goals.append(int(away_goals))
    team.this_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

def fill_last_season_avg_goals(team, season, understat):
    season_goals = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                home_goals = match['goals'].get('h')
                if home_goals is not None:
                    season_goals.append(int(home_goals))
            elif match['a']['short_title'] == team.short_title:
                away_goals = match['goals'].get('a')
                if away_goals is not None:
                    season_goals.append(int(away_goals))
    team.last_season_avg_goals = np.mean(season_goals) if season_goals else 0.0

def fill_total_avg_goals(team):
    total_goals = []
    for match in team.matches:
        if 'goals' in match:
            if match['h']['short_title'] == team.short_title:
                home_goals = match['goals'].get('h')
                if home_goals is not None:
                    total_goals.append(int(home_goals))
            elif match['a']['short_title'] == team.short_title:
                away_goals = match['goals'].get('a')
                if away_goals is not None:
                    total_goals.append(int(away_goals))
    team.total_avg_goals = np.mean(total_goals) if total_goals else 0.0

def fill_last_5_matches_avg_xg(team):
    last_5_matches_xg = []
    for match in team.matches[-5:]:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                home_xg = match['xG'].get('h')
                if home_xg is not None:
                    last_5_matches_xg.append(float(home_xg))
            elif match['a']['short_title'] == team.short_title:
                away_xg = match['xG'].get('a')
                if away_xg is not None:
                    last_5_matches_xg.append(float(away_xg))
    team.last_5_matches_avg_xg = np.mean(last_5_matches_xg) if last_5_matches_xg else 0.0

def fill_this_season_avg_xg(team, season, understat):
    season_xg = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                home_xg = match['xG'].get('h')
                if home_xg is not None:
                    season_xg.append(float(home_xg))
            elif match['a']['short_title'] == team.short_title:
                away_xg = match['xG'].get('a')
                if away_xg is not None:
                    season_xg.append(float(away_xg))
    team.this_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

def fill_last_season_avg_xg(team, season, understat):
    season_xg = []
    matches = team.get_match_data(season, understat)
    for match in matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                home_xg = match['xG'].get('h')
                if home_xg is not None:
                    season_xg.append(float(home_xg))
            elif match['a']['short_title'] == team.short_title:
                away_xg = match['xG'].get('a')
                if away_xg is not None:
                    season_xg.append(float(away_xg))
    team.last_season_avg_xg = np.mean(season_xg) if season_xg else 0.0

def fill_total_avg_xg(team):
    total_xg = []
    for match in team.matches:
        if 'xG' in match:
            if match['h']['short_title'] == team.short_title:
                home_xg = match['xG'].get('h')
                if home_xg is not None:
                    total_xg.append(float(home_xg))
            elif match['a']['short_title'] == team.short_title:
                away_xg = match['xG'].get('a')
                if away_xg is not None:
                    total_xg.append(float(away_xg))
    team.total_avg_xg = np.mean(total_xg) if total_xg else 0.0
