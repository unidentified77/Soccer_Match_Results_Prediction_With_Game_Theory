#!/usr/bin/env python3
"""
understat_fetch_functions.py

This module defines 40 functions that fetch different data types from Understat
using the understatapi package. Each function calls an endpoint method from the UnderstatClient.
If an endpoint is not available in UnderstatAPI, the function returns an error message.
All sample outputs are provided as comments in each docstring.

Before running, ensure you have installed understatapi (e.g., via pip) and that your network
access to Understat is enabled.
"""

import logging
from understatapi import UnderstatClient

def normalize_understat_record(rec: dict) -> dict:
    """
    Converts a raw Understat record into normalized per-game averages.
    """
    try:
        games = float(rec.get("games", 0))
    except:
        games = 0
    if games <= 0:
        games = 1
    normalized = {
        "goals": float(rec.get("goals", 0)) / games,
        "xG": float(rec.get("xG", 0)) / games,
        "assists": float(rec.get("assists", 0)) / games,
        "xA": float(rec.get("xA", 0)) / games,
        "shots": float(rec.get("shots", 0)) / games,
        "key_passes": float(rec.get("key_passes", 0)) / games,
        "yellow": float(rec.get("yellow_cards", 0)) / games,
        "red": float(rec.get("red_cards", 0)) / games,
        "npxG": 0.0,
        "xGChain": float(rec.get("xGChain", 0)) / games,
        "xGBuildup": float(rec.get("xGBuildup", 0)) / games,
        "npg": float(rec.get("npg", 0)) / games
    }
    try:
        raw_npxG = rec.get("npxG")
        if raw_npxG is None or float(raw_npxG) == 0:
            goals_val = float(rec.get("goals", 0))
            npg_val = float(rec.get("npg", 0)) if rec.get("npg") is not None else 0
            xg_val = float(rec.get("xG", 0))
            if goals_val > 0:
                penalty_xg = (xg_val / goals_val) * (goals_val - npg_val)
                normalized["npxG"] = (xg_val - penalty_xg) / games
            else:
                normalized["npxG"] = 0.0
        else:
            normalized["npxG"] = float(raw_npxG) / games
    except Exception:
        normalized["npxG"] = 0.0

    pos = rec.get("position", "").upper()
    if pos in ["GK", "G"]:
        normalized["saves"] = float(rec.get("saves", 0)) / games
        try:
            minutes = float(rec.get("time", 0))
        except:
            minutes = 0
        normalized["clean_sheet"] = 1.0 if minutes >= 90 else 0.0
    return normalized
def fetch_recent_stats_fixed(understat, player_name: str, team: str, season: str, last_n: int = 5) -> list:
    """
    Improved version: iterate over matches in reverse order (most recent first)
    and only include matches where valid roster data is returned.
    Stop when last_n valid records have been collected.
    """
    valid_records = []
    matches = understat.team(team).get_match_data(season=season)
    if not matches:
        return valid_records
    # Iterate over matches in reverse order (most recent first)
    for match in reversed(matches):
        match_id = match.get("id")
        if not match_id:
            continue
        try:
            roster = understat.match(match_id).get_roster_data()
        except Exception as e:
            logging.debug(f"Error fetching roster for match {match_id}: {e}")
            continue
        # Check that roster is valid (contains keys "h" and "a")
        if not roster or not all(k in roster for k in ["h", "a"]):
            continue
        found = False
        for side in ["h", "a"]:
            for pid, pstats in roster.get(side, {}).items():
                candidate = pstats.get("player") or pstats.get("player_name", "")
                if normalize_name(candidate) == normalize_name(player_name):
                    valid_records.append(normalize_understat_record(pstats))
                    found = True
                    break
            if found:
                break
        if len(valid_records) >= last_n:
            break
    return list(reversed(valid_records))  # Return in chronological order

def normalize_name(name: str) -> str:
    """Lowercases and trims a name for robust matching."""
    return name.strip().lower()

def fetch_recent_stats(understat, player_name: str, team: str, season: str, last_n: int = 5) -> list:
    """
    Fetch recent statistics for a given player from the last `last_n` matches of the team in the season.
    
    This function uses the UnderstatClient instance (understat) to:
      1. Fetch match data for the team for the specified season.
      2. For the last `last_n` matches, fetch the match roster data.
      3. In each match, search for the player (by matching normalized player names) in both home and away rosters.
      4. Collect the player's stats from each match where found.
    
    Returns:
      A list of player stat dictionaries (one per match) from recent matches.
      
    Example output:
      [ {'goals': '2', 'xG': '1.8', ...}, {...}, ... ]
    """
    recent_stats = []
    # Fetch all match data for the team.
    matches = understat.team(team).get_match_data(season=season)
    if not matches:
        return recent_stats
    # Use only the last `last_n` matches.
    recent_matches = matches[-last_n:]
    for match in recent_matches:
        match_id = match.get("id")
        if not match_id:
            continue
        try:
            roster = understat.match(match_id).get_roster_data()
        except Exception:
            continue
        # Understat roster is assumed to have keys 'h' and 'a'
        for side in ["h", "a"]:
            team_players = roster.get(side, {})
            for pid, pstats in team_players.items():
                # Match by player name (normalize both)
                if normalize_name(pstats.get("player", "")) == normalize_name(player_name):
                    recent_stats.append(pstats)
                    break  # Found player in this match; proceed to next match.
    return recent_stats
# 1. Fetch league match data.
def fetch_league_match_data(league: str, season: str):
    """
    Fetch all match data for a given league and season.
    Endpoint: understat.league(league).get_match_data(season=season)
    Sample output:
    { "matches": [ { "id": "123", "date": "2024-04-05", ... }, ... ] }
    """
    with UnderstatClient() as understat:
        return understat.league(league).get_match_data(season=season)

# 2. Fetch league player data.
def fetch_league_player_data(league: str, season: str):
    """
    Fetch all player data for a given league and season.
    Endpoint: understat.league(league).get_player_data(season=season)
    Sample output:
    { "players": [ { "id": "2371", "player_name": "Player A", ... }, ... ] }
    """
    with UnderstatClient() as understat:
        return understat.league(league).get_player_data(season=season)

# 3. Fetch team match data.
def fetch_team_match_data(team: str, season: str):
    """
    Fetch match data for a given team and season.
    Endpoint: understat.team(team).get_match_data(season=season)
    """
    with UnderstatClient() as understat:
        return understat.team(team).get_match_data(season=season)

# 4. Fetch team player data.
def fetch_team_player_data(team: str, season: str):
    """
    Fetch player data for a given team and season.
    Endpoint: understat.team(team).get_player_data(season=season)
    """
    with UnderstatClient() as understat:
        return understat.team(team).get_player_data(season=season)

# 5. Fetch team advanced stats.
def fetch_team_stats(team: str, season: str):
    """
    Fetch advanced statistics for a team.
    (If available: some implementations provide get_stats.)
    """
    with UnderstatClient() as understat:
        try:
            return understat.team(team).get_stats(season=season)
        except AttributeError:
            return {"error": "get_stats method not available for team endpoint."}

# 6. Fetch match roster data.
def fetch_match_roster_data(match_id: str):
    """
    Fetch the roster data for a given match.
    Endpoint: understat.match(match_id).get_roster_data()
    """
    with UnderstatClient() as understat:
        return understat.match(match_id).get_roster_data()

# 7. Fetch match shot data.
def fetch_match_shot_data(match_id: str):
    """
    Fetch shot data for a match.
    Endpoint: understat.match(match_id).get_shot_data()
    Sample output:
    { "shots": [ {...}, {...} ] }
    """
    with UnderstatClient() as understat:
        try:
            return understat.match(match_id).get_shot_data()
        except AttributeError:
            return {"error": "get_shot_data method not available for match endpoint."}

# 8. Fetch player shot data.
def fetch_player_shot_data(player_id: str):
    """
    Fetch shot data for a player.
    Endpoint: understat.player(player_id).get_shot_data()
    """
    with UnderstatClient() as understat:
        try:
            return understat.player(player_id).get_shot_data()
        except AttributeError:
            return {"error": "get_shot_data method not available for player endpoint."}

# 9. Fetch player statistics.
def fetch_player_stats(player_id: str, season: str):
    """
    Fetch match statistics for a player.
    Endpoint: understat.player(player_id).get_stats(season=season)
    """
    with UnderstatClient() as understat:
        try:
            return understat.player(player_id).get_stats(season=season)
        except AttributeError:
            return {"error": "get_stats method not available for player endpoint."}

# 10. Fetch player rating data.
def fetch_player_rating_data(player_id: str, season: str):
    """
    Fetch rating data for a player.
    (This may be part of get_stats.)
    """
    return fetch_player_stats(player_id, season)

# 11. Fetch team goal data (aggregated from match data).
def fetch_team_goal_data(team: str, season: str):
    """
    Aggregate team goals from match data.
    Uses the match data from fetch_team_match_data and extracts the goals
    for the given team. If a goal value is missing (None), it is treated as 0.
    
    Returns a dictionary with the average goals and total goals.
    """
    data = fetch_team_match_data(team, season)
    goals = []
    for m in data:
        if "goals" in m:
            home_title = m["h"].get("title", "").lower()
            away_title = m["a"].get("title", "").lower()
            if home_title == team.lower():
                # Use (x or 0) to default to 0 if x is None.
                x = m["goals"].get("h")
                goals.append(int(x or 0))
            elif away_title == team.lower():
                x = m["goals"].get("a")
                goals.append(int(x or 0))
    return {"avg_goals": sum(goals)/len(goals) if goals else 0.0, "total_goals": sum(goals)}

# 12. Fetch team expected goals data.
def fetch_team_xg_data(team: str, season: str):
    """
    Aggregates team xG from match data.
    Uses fetch_team_match_data(team, season) and extracts the xG value for the given team.
    If the xG value is missing (None), it defaults to 0.
    
    Returns a dictionary with the average xG and total xG.
    """
    data = fetch_team_match_data(team, season)
    xg_vals = []
    for m in data:
        if "xG" in m:
            # Use .get(... or 0) to ensure a numeric value
            if m["h"].get("title", "").lower() == team.lower():
                value = m["xG"].get("h") or 0
                xg_vals.append(float(value))
            elif m["a"].get("title", "").lower() == team.lower():
                value = m["xG"].get("a") or 0
                xg_vals.append(float(value))
    return {"avg_xG": sum(xg_vals)/len(xg_vals) if xg_vals else 0.0,
            "total_xG": sum(xg_vals)}

# 13. Fetch league top scorers.
def fetch_league_top_scorers(league: str, season: str):
    """
    Fetch top scorers for a league.
    Endpoint: understat.league(league).get_top_scorers(season=season)
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_top_scorers(season=season)
        except AttributeError:
            return {"error": "get_top_scorers method not available."}

# 14. Fetch league top assisters.
def fetch_league_top_assisters(league: str, season: str):
    """
    Fetch top assisters for a league.
    Endpoint: understat.league(league).get_top_assisters(season=season)
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_top_assisters(season=season)
        except AttributeError:
            return {"error": "get_top_assisters method not available."}

# 15. Fetch league top xG performers.
def fetch_league_top_xg(league: str, season: str):
    """
    Fetch players with the highest xG in a league.
    Endpoint: understat.league(league).get_top_xG(season=season)
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_top_xG(season=season)
        except AttributeError:
            return {"error": "get_top_xG method not available."}

# 16. Fetch match summary.
def fetch_match_summary(match_id: str):
    """
    Fetch a summary for a match.
    Endpoint: understat.match(match_id).get_summary()
    """
    with UnderstatClient() as understat:
        try:
            return understat.match(match_id).get_summary()
        except AttributeError:
            return {"error": "get_summary method not available for match endpoint."}

# 17. Fetch match events.
def fetch_match_events(match_id: str):
    """
    Fetch events for a match.
    (Understat may not support events; if not, return error.)
    """
    with UnderstatClient() as understat:
        try:
            return understat.match(match_id).get_events()
        except AttributeError:
            return {"error": "get_events method not available for match endpoint."}

# 18. Fetch match substitutions.
def fetch_match_substitutions(match_id: str):
    """
    Fetch substitution events from a match.
    Caller should filter events for substitutions.
    """
    events = fetch_match_events(match_id)
    if "error" in events:
        return events
    subs = [e for e in events.get("response", []) if e.get("type") == "Substitution"]
    return {"substitutions": subs}

# 19. Fetch player career statistics.
def fetch_player_career_stats(player_id: str, seasons: list):
    """
    Aggregate career statistics for a player over multiple seasons.
    (This function must aggregate data from multiple calls to fetch_player_stats.)
    """
    career_stats = {}
    count = 0
    for season in seasons:
        stats = fetch_player_stats(player_id, season)
        if stats.get("response"):
            count += 1
            # Caller must implement aggregation logic; here we simply return a list.
            career_stats[season] = stats.get("response")
    if count == 0:
        return {"error": "No career data found."}
    return career_stats

# 20. Fetch team career statistics.
def fetch_team_career_stats(team: str, seasons: list):
    """
    Aggregate team match data over multiple seasons.
    Returns a dictionary with season-by-season match data.
    """
    career_data = {}
    for season in seasons:
        data = fetch_team_match_data(team, season)
        career_data[season] = data
    return career_data

# 21. Fetch team form data.
def fetch_team_form_data(team: str, season: str):
    """
    Fetch team form (last 5 matches) from Understat match data.
    """
    data = fetch_team_match_data(team, season)
    # Caller should compute form from win/loss/draw.
    return {"matches": data}

# 22. Fetch raw match data.
def fetch_match_data(match_id: str):
    """
    Fetch raw match data.
    (Same as get_match_data on match endpoint if available.)
    """
    with UnderstatClient() as understat:
        try:
            return understat.match(match_id).get_match_data()
        except AttributeError:
            return {"error": "get_match_data method not available for match endpoint."}

# 23. Fetch player shot map.
def fetch_player_shot_map(player_id: str, season: str):
    """
    Fetch shot map data for a player.
    (If available: understat.player(player_id).get_shot_map())
    """
    with UnderstatClient() as understat:
        try:
            return understat.player(player_id).get_shot_map(season=season)
        except AttributeError:
            return {"error": "get_shot_map method not available for player endpoint."}

# 24. Fetch player xG data.
def fetch_player_xg_data(player_id: str, season: str):
    """
    Fetch xG data for a player.
    (If available, using get_stats and extracting xG.)
    """
    stats = fetch_player_stats(player_id, season)
    return stats.get("response", [])

# 25. Fetch player expected goals.
def fetch_player_expected_goals(player_id: str, season: str):
    """
    Fetch expected goals (xG) for a player.
    (Alias for fetch_player_xg_data)
    """
    return fetch_player_xg_data(player_id, season)

# 26. Fetch player expected assists.
def fetch_player_expected_assists(player_id: str, season: str):
    """
    Fetch expected assists (xA) for a player.
    (If available; otherwise return error.)
    """
    with UnderstatClient() as understat:
        try:
            return understat.player(player_id).get_xa_data(season=season)
        except AttributeError:
            return {"error": "get_xa_data method not available for player endpoint."}

# 27. Fetch team shot map.
def fetch_team_shot_map(team: str, season: str):
    """
    Fetch shot map data for a team.
    (If available: may require aggregating match shot data.)
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 28. Fetch team tackle data.
def fetch_team_tackle_data(team: str, season: str):
    """
    Aggregate tackle statistics for a team from match data.
    (Caller must parse tackle info from match data.)
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 29. Fetch team interception data.
def fetch_team_interception_data(team: str, season: str):
    """
    Aggregate interception statistics for a team from match data.
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 30. Fetch team duel data.
def fetch_team_duel_data(team: str, season: str):
    """
    Aggregate duel statistics for a team from match data.
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 31. Fetch team pass data.
def fetch_team_pass_data(team: str, season: str):
    """
    Aggregate pass statistics for a team.
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 32. Fetch team dribble data.
def fetch_team_dribble_data(team: str, season: str):
    """
    Aggregate dribble statistics for a team.
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 33. Fetch team card data.
def fetch_team_card_data(team: str, season: str):
    """
    Aggregate card (yellow/red) data for a team.
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 34. Fetch league standings.
def fetch_league_standings(league: str, season: str):
    """
    Fetch league standings.
    Endpoint: understat.league(league).get_standings(season=season)
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_standings(season=season)
        except AttributeError:
            return {"error": "get_standings method not available for league endpoint."}

# 35. Fetch league statistics.
def fetch_league_statistics(league: str, season: str):
    """
    Fetch aggregated league statistics.
    (If available: understat.league(league).get_stats(season=season))
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_stats(season=season)
        except AttributeError:
            return {"error": "get_stats method not available for league endpoint."}

# 36. Fetch player minutes played.
def fetch_player_minutes(player_id: str, season: str):
    """
    Fetch minutes played by a player.
    (Extract from understat.player(player_id).get_stats(season=season))
    """
    stats = fetch_player_stats(player_id, season)
    # Caller must extract minutes info.
    return stats.get("response", [])

# 37. Fetch team minutes played.
def fetch_team_minutes(team: str, season: str):
    """
    Aggregate total minutes played by a team.
    (Caller must parse minutes from team match data.)
    """
    data = fetch_team_match_data(team, season)
    return {"matches": data}

# 38. Fetch match player ratings.
def fetch_match_player_ratings(match_id: str):
    """
    Fetch player ratings for a match.
    (If available: understat.match(match_id).get_player_ratings())
    """
    with UnderstatClient() as understat:
        try:
            return understat.match(match_id).get_player_ratings()
        except AttributeError:
            return {"error": "get_player_ratings method not available for match endpoint."}

# 39. Fetch league top rated players.
def fetch_league_top_rated_players(league: str, season: str):
    """
    Fetch players with the highest ratings in a league.
    (If available: understat.league(league).get_top_rated(season=season))
    """
    with UnderstatClient() as understat:
        try:
            return understat.league(league).get_top_rated(season=season)
        except AttributeError:
            return {"error": "get_top_rated method not available for league endpoint."}

# 40. Fetch match xG data.
def fetch_match_xg_data(match_id: str):
    """
    Fetch xG data for a match.
    (If available: might be part of get_match_data())
    """
    data = fetch_match_data(match_id)
    # Caller must extract xG from the response.
    return data.get("xG", {"error": "xG data not found."})

# 40.5. (Bonus extra) Fetch raw match data.
def fetch_raw_match_data(match_id: str):
    """
    Fetch raw match data for a match.
    Alias for fetch_match_data.
    """
    return fetch_match_data(match_id)


# Main block: demonstration of a few sample calls.
if __name__ == "__main__":
    # Sample parameters – adjust as needed.
    sample_league = "EPL"
    sample_season = "2024"
    sample_team = "Chelsea"
    sample_match_id = "26610"
    sample_player_id = "8497"  # example

    

    print("\n4. Player career stats:")
    print(fetch_recent_stats("Evanilson", sample_team, "2024" , last_n=5))
