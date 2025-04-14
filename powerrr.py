import logging
import requests
import pandas as pd
import difflib
from understatapi import UnderstatClient

# --- CONFIG ---
API_KEY = "078dfd2522b94892b4675b57bd810999"
API_HOST = "v3.football.api-sports.io"
BASE_URL = f"https://{API_HOST}"
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print("[DEBUG]", msg)

# --------------------------------------------------------
# 1) FETCH LINEUPS (with extra debug logs)
# --------------------------------------------------------
def fetch_lineups(fixture_id: int) -> list:
    """
    Hit API-Football: /fixtures/lineups?fixture={fixture_id}
    Typically returns a list with up to 2 items (home/away):
      {
        "team": { "id":..., "name":..., ... },
        "coach": { ... },
        "formation": "4-3-3" or None,
        "startXI": [ { "player": {...} }, ... ],
        "substitutes": [ { "player": {...} }, ... ]
      }
    For fixture_id=1208332, the API currently returns formation=null
    and no 'startXI' in the JSON. We'll add debug logs to confirm.
    """
    url = f"{BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    headers = {
        "x-apisports-key": API_KEY,
        "x-apisports-host": API_HOST
    }
    debug_print(f"[fetch_lineups] Requesting URL={url}")
    r = requests.get(url, headers=headers)
    data = r.json()

    # Debug: Show the raw top-level structure so we see what we got
    debug_print(f"[fetch_lineups] Raw response keys={list(data.keys())}, results={data.get('results')}")
    if "response" in data:
        debug_print(f"[fetch_lineups] # of lineups in 'response': {len(data['response'])}")
    else:
        debug_print("[fetch_lineups] No 'response' key in JSON.")

    return data.get("response", [])

# --------------------------------------------------------
# 2) FETCH UNDERSTAT PLAYER DATA (with debug logs)
# --------------------------------------------------------
def fetch_team_player_data_from_understat(team_name: str, season="2024"):
    """
    Use understatapi to get advanced stats for each player of a given team in a given season.
    We'll add debug logs and gracefully handle errors if team not found, etc.
    """
    from understatapi import UnderstatClient
    out = []
    debug_print(f"[Understat] Fetching player data for team='{team_name}', season='{season}'")
    try:
        with UnderstatClient() as understat:
            player_data = understat.team(team=team_name).get_player_data(season=season)
        debug_print(f"[Understat] Retrieved {len(player_data)} players for {team_name}")
        for p in player_data:
            pname = p.get("player_name", "")
            games = float(p.get("games", 0))
            goals = float(p.get("goals", 0))
            xG = float(p.get("xG", 0))
            assists = float(p.get("assists", 0))
            shots = float(p.get("shots", 0))
            position = p.get("position", "F")

            if games > 0:
                avg_goals = goals / games
                avg_xg = xG / games
                avg_assists = assists / games
                avg_shots = shots / games
            else:
                avg_goals = 0.0
                avg_xg = 0.0
                avg_assists = 0.0
                avg_shots = 0.0

            out.append({
                "player_name": pname,
                "position": position,
                "avg_goals": avg_goals,
                "avg_xg": avg_xg,
                "avg_assists": avg_assists,
                "avg_shots": avg_shots
            })
    except Exception as e:
        debug_print(f"[Understat] ERROR fetching data for {team_name}, reason={e}")
    return out

# --------------------------------------------------------
# 3) NAME MATCHING + PLAYER POWER
# --------------------------------------------------------
def match_lineup_player_to_understat(lineup_player_name: str, understat_players: list) -> dict:
    """
    Use difflib to match the lineup name to an Understat player record.
    Returns the best match or None if no match found.
    We'll log debug info if we can't find anything.
    """
    if not understat_players:
        debug_print(f"[match] No Understat data available to match '{lineup_player_name}'")
        return None

    all_us_names = [p["player_name"] for p in understat_players]
    best_match = difflib.get_close_matches(lineup_player_name, all_us_names, n=1, cutoff=0.3)
    if not best_match:
        debug_print(f"[match] No close match found for '{lineup_player_name}' in Understat player list.")
        return None

    # Return the corresponding record
    matched_name = best_match[0]
    for rec in understat_players:
        if rec["player_name"] == matched_name:
            debug_print(f"[match] '{lineup_player_name}' matched with '{matched_name}' from Understat.")
            return rec
    return None

def calculate_player_power(udata: dict) -> float:
    """
    Weighted formula for average goals, xG, assists, etc. 
    Modify weights to your preference. We'll add debug logs.
    """
    if not udata:
        return 0.0

    pos = udata.get("position", "F").upper()
    avg_goals = udata.get("avg_goals", 0.0)
    avg_xg = udata.get("avg_xg", 0.0)
    avg_assists = udata.get("avg_assists", 0.0)
    avg_shots = udata.get("avg_shots", 0.0)

    base = 5.0
    if pos in ["F","FW","ST"]:
        base += (avg_goals * 4) + (avg_xg * 2.5) + (avg_assists * 1.5)
    elif pos in ["M","MF","AM","CM"]:
        base += (avg_goals * 2) + (avg_xg * 2) + (avg_assists * 2)
    elif pos in ["D","DF","CB","LB","RB"]:
        # If we had defensive stats, we'd weigh them here. We'll do a partial approach:
        base += (avg_goals * 1.0) + (avg_shots * 0.5)
    elif pos in ["GK"]:
        # We typically have no GK stats from Understat, so let's keep it minimal:
        base += 0.0
    else:
        base += (avg_goals * 2.0) + (avg_xg * 2.0)

    final = round(base, 2)
    debug_print(f"[calc_player_power] For pos={pos}, goals={avg_goals}, xG={avg_xg}, => {final}")
    return final

# --------------------------------------------------------
# 4) MAIN DEMO: Check fixture=1208332 lineups & do power
# --------------------------------------------------------
def main():
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

    fixture_id = 1208332
    debug_print(f"[main] Starting player power check for fixture={fixture_id}")

    # 1) Get lineups from API-Football
    lineups_data = fetch_lineups(fixture_id)
    if not lineups_data:
        debug_print("[main] No lineup data found at all => cannot do player power.")
        return

    # We'll parse each team chunk separately
    for chunk in lineups_data:
        team_id = chunk["team"]["id"]
        team_name = chunk["team"]["name"]
        formation = chunk.get("formation")
        debug_print(f"[main] Team ID={team_id}, name={team_name}, formation={formation}")

        # 'startXI' might be missing as we saw => let's see if it is there
        start_xi_list = chunk.get("startXI", [])
        if not start_xi_list:
            debug_print("[main] 'startXI' is empty or missing => The API has no lineup details.")
        else:
            debug_print(f"[main] Found {len(start_xi_list)} players in startXI for {team_name}")

        # 2) Also fetch Understat data for that team
        understat_data = fetch_team_player_data_from_understat(team_name, season="2024")

        # 3) For each player in startXI, match + calc power
        for pinfo in start_xi_list:
            # Typically: pinfo = {"player":{"id":..., "name":..., "pos":..., "number":...}}
            lineup_name = pinfo["player"]["name"]
            matched = match_lineup_player_to_understat(lineup_name, understat_data)
            if matched:
                power = calculate_player_power(matched)
            else:
                debug_print(f"[main] No matched Understat record => power=0 for {lineup_name}")
                power = 0.0
            print(f"TEAM={team_name} | Player={lineup_name} => POWER={power}")

        print("--------------")

if __name__ == "__main__":
    main()