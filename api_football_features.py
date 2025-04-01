# api_football_features.py

import requests
from datetime import datetime, timedelta

DEBUG = True  # Turn on/off debug prints more easily
def debug_print(msg):
    if DEBUG:
        print(msg)

BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",  # replace with your real key
    "x-apisports-host": "v3.football.api-sports.io"
}


def fetch_lineup_strength(fixture_id: int) -> dict:
    """
    Retrieve the lineup for a given fixture and compute an indicator of lineup strength.
    Returns a dict with { "fixture_id": <id>, "strength_score": {team_name: count_of_stars} }
    """
    url = f"{BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    debug_print(f"[fetch_lineup_strength] GET {url}")
    response = requests.get(url, headers=API_HEADERS)
    debug_print(f"  => Status code: {response.status_code}")
    try:
        data = response.json()
        debug_print(f"  => JSON response (partial): {str(data)[:600]} ...")
    except:
        debug_print("  => Could not parse JSON!")
        return {"fixture_id": fixture_id, "strength_score": None}

    lineup_strength_info = {"fixture_id": fixture_id, "strength_score": None}
    if data.get("response"):
        lineups = data["response"]
        strength_scores = {}
        for lineup in lineups:
            team_name = lineup.get("team", {}).get("name")
            starting_players = lineup.get("startXI", [])
            top_players_count = 0
            for player_entry in starting_players:
                player_name = player_entry.get("player", {}).get("name", "")
                # Example star names
                if player_name in ["Harry Kane", "Mohamed Salah", "Erling Haaland"]:
                    top_players_count += 1
            strength_scores[team_name] = top_players_count
        lineup_strength_info["strength_score"] = strength_scores
    return lineup_strength_info


def fetch_injuries(fixture_id: int, team_id: int, season: int = 2024) -> list:
    """
    Return a list of injured players specifically for `fixture_id` (not the whole season).
    API-Football's /injuries?team=...&season=... gives a season's worth of injuries, 
    each with a 'fixture': { 'id': ..., 'date': ... }
    We filter to keep only injuries where `fixture.id == fixture_id`.
    If none match, we return an empty list.
    """
    url = f"{BASE_URL}/injuries?team={team_id}&season={season}"
    debug_print(f"[fetch_injuries] GET {url}")
    response = requests.get(url, headers=API_HEADERS)
    debug_print(f"  => Status code: {response.status_code}")
    try:
        data = response.json()
        debug_print(f"  => JSON response (partial): {str(data)[:600]} ...")
    except:
        debug_print("  => Could not parse JSON!")
        return []
    injured_players = []
    if data.get("response"):
        for injury_item in data["response"]:
            # The API typically includes "fixture": {"id":some_id, "date":..., ...}
            fix = injury_item.get("fixture", {})
            if fix.get("id") == fixture_id:
                player = injury_item.get("player", {})
                p_name = player.get("name")
                if p_name:
                    injured_players.append(p_name)
    debug_print(f"  => Found {len(injured_players)} injured players for fixture_id={fixture_id}")
    return injured_players


def fetch_odds(fixture_id: int) -> dict:
    """
    Return odds for "Match Winner" (1X2) from the first bookmaker found.
    We look up 'value' keys: "Home", "Draw", "Away" rather than 'label'.
    """
    url = f"{BASE_URL}/odds?fixture={fixture_id}"
    debug_print(f"[fetch_odds] GET {url}")
    response = requests.get(url, headers=API_HEADERS)
    debug_print(f"  => Status code: {response.status_code}")
    try:
        data = response.json()
        debug_print(f"  => JSON response (partial): {str(data)[:600]} ...")
    except:
        debug_print("  => Could not parse JSON!")
        return {}
    odds_data = {}
    if data.get("response"):
        try:
            first_bookmaker = data["response"][0]
            bets = first_bookmaker.get("bookmakers", [])[0].get("bets", [])
            for bet in bets:
                if bet.get("name") == "Match Winner":
                    for odd_item in bet.get("values", []):
                        # Example: odd_item={"value":"Home","odd":"1.50"}
                        v = odd_item.get("value")
                        o = odd_item.get("odd")
                        if v in ["Home", "Draw", "Away"] and o is not None:
                            odds_data[v] = float(o)
        except Exception as ex:
            debug_print(f"  => Error extracting odds: {ex}")
    return odds_data


def fetch_team_standing(team_id: int, league_id: int = 39, season: int = 2024) -> dict:
    url = f"{BASE_URL}/standings?league={league_id}&season={season}"
    debug_print(f"[fetch_team_standing] GET {url}")
    response = requests.get(url, headers=API_HEADERS)
    debug_print(f"  => Status code: {response.status_code}")
    try:
        data = response.json()
        debug_print(f"  => JSON response (partial): {str(data)[:600]} ...")
    except:
        debug_print("  => Could not parse JSON!")
        return {}
    team_standing_info = {}
    if data.get("response"):
        standings_table = data["response"][0].get("league", {}).get("standings", [])
        if standings_table:
            # standings_table[0] => list of rank entries
            for entry in standings_table[0]:
                if entry.get("team", {}).get("id") == team_id:
                    team_standing_info = {
                        "rank": entry.get("rank"),
                        "points": entry.get("points"),
                        "goals_for": entry["all"]["goals"]["for"],
                        "goals_against": entry["all"]["goals"]["against"],
                        "goal_diff": entry["goalsDiff"],
                        "form": entry.get("form")
                    }
                    break
    debug_print(f"  => Team standing found: {team_standing_info}")
    return team_standing_info


def fetch_rest_days(team_id: int, fixture_date: str) -> int:
    """
    We pass from=some_start_of_season and to=<fixture_date> to get all the team's 
    completed matches. Then we find the last one prior to fixture_date. 
    Return # of days difference. If none, return None.
    """
    debug_print(f"[fetch_rest_days] team_id={team_id}, fixture_date={fixture_date}")

    # remove any trailing "Z" or "+00:00"
    if "Z" in fixture_date:
        fixture_date = fixture_date.replace("Z", "")
    if "+" in fixture_date:
        fixture_date = fixture_date.split("+")[0]
    debug_print(f"  => cleaned fixture_date: {fixture_date}")

    # Attempt to parse ISO date
    try:
        match_dt = datetime.fromisoformat(fixture_date)
    except Exception as e:
        debug_print(f"  => Could not parse fixture_date: {e}")
        return None

    # Build the from date as e.g. August 1st of the same year => or earlier
    # because the season typically starts ~ August
    from_str = f"{match_dt.year}-08-01"
    to_str   = match_dt.strftime("%Y-%m-%d")
    url = (f"{BASE_URL}/fixtures?team={team_id}&from={from_str}&to={to_str}"
           f"&season={match_dt.year}&status=FT")
    debug_print(f"  => GET {url}")
    response = requests.get(url, headers=API_HEADERS)
    debug_print(f"  => Status code: {response.status_code}")
    try:
        data = response.json()
        debug_print(f"  => JSON response (partial): {str(data)[:600]} ...")
    except:
        debug_print("  => Could not parse JSON!")
        return None

    last_game_date = None
    if data.get("response"):
        # We only want fixtures that ended prior to match_dt
        valid_past_games = []
        for fix in data["response"]:
            fix_dt_str = fix["fixture"]["date"]  # "2024-08-30T16:00:00+00:00"
            try:
                fix_dt = datetime.fromisoformat(fix_dt_str.replace("Z", "+00:00").split("+")[0])
                if fix_dt < match_dt:
                    valid_past_games.append(fix)
            except:
                pass
        # sort descending by date
        valid_past_games.sort(key=lambda x: x["fixture"]["date"], reverse=True)
        if valid_past_games:
            last_game_date_str = valid_past_games[0]["fixture"]["date"]
            try:
                last_game_date = datetime.fromisoformat(last_game_date_str.replace("Z", "+00:00").split("+")[0])
            except:
                pass

    if last_game_date:
        rest_duration = match_dt - last_game_date
        debug_print(f"  => last_game_date={last_game_date}, rest_duration={rest_duration.days} days")
        return rest_duration.days
    else:
        debug_print("  => No previous FT game found prior to fixture_date.")
        return None