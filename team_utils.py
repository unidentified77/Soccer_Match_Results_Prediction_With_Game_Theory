# team_utils.py

from utils import np

def fill_last_5_matches_avg_goals(team):
    arr = []
    for match in team.matches[-5:]:
        if "goals" in match:
            if match["h"]["short_title"] == team.short_title:
                x = match["goals"].get("h")
                if x is not None:
                    arr.append(int(x))
            elif match["a"]["short_title"] == team.short_title:
                x = match["goals"].get("a")
                if x is not None:
                    arr.append(int(x))
    team.last_5_matches_avg_goals = np.mean(arr) if arr else 0.0

def fill_this_season_avg_goals(team, season, understat):
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "goals" in m:
            if m["h"]["short_title"] == team.short_title:
                x = m["goals"].get("h")
                if x:
                    arr.append(int(x))
            elif m["a"]["short_title"] == team.short_title:
                x = m["goals"].get("a")
                if x:
                    arr.append(int(x))
    team.this_season_avg_goals = np.mean(arr) if arr else 0.0

def fill_last_season_avg_goals(team, season, understat):
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "goals" in m:
            if m["h"]["short_title"] == team.short_title:
                x = m["goals"].get("h")
                if x:
                    arr.append(int(x))
            elif m["a"]["short_title"] == team.short_title:
                x = m["goals"].get("a")
                if x:
                    arr.append(int(x))
    team.last_season_avg_goals = np.mean(arr) if arr else 0.0

def fill_total_avg_goals(team):
    arr = []
    for m in team.matches:
        if "goals" in m:
            if m["h"]["short_title"] == team.short_title:
                x = m["goals"].get("h")
                if x:
                    arr.append(int(x))
            elif m["a"]["short_title"] == team.short_title:
                x = m["goals"].get("a")
                if x:
                    arr.append(int(x))
    team.total_avg_goals = np.mean(arr) if arr else 0.0

def fill_last_5_matches_avg_xg(team):
    arr = []
    for m in team.matches[-5:]:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v is not None:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v is not None:
                    arr.append(float(v))
    team.last_5_matches_avg_xg = np.mean(arr) if arr else 0.0

def fill_this_season_avg_xg(team, season, understat):
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v:
                    arr.append(float(v))
    team.this_season_avg_xg = np.mean(arr) if arr else 0.0

def fill_last_season_avg_xg(team, season, understat):
    arr = []
    data = team.get_match_data(season, understat)
    for m in data:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v:
                    arr.append(float(v))
    team.last_season_avg_xg = np.mean(arr) if arr else 0.0

def fill_total_avg_xg(team):
    arr = []
    for m in team.matches:
        if "xG" in m:
            if m["h"]["short_title"] == team.short_title:
                v = m["xG"].get("h")
                if v:
                    arr.append(float(v))
            elif m["a"]["short_title"] == team.short_title:
                v = m["xG"].get("a")
                if v:
                    arr.append(float(v))
    team.total_avg_xg = np.mean(arr) if arr else 0.0