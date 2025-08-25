#!/usr/bin/env python3
"""
api_sports_fetch_functions.py

This module defines 50 functions that fetch data from API‑Football.
Many endpoints have changed names over time; here we have "fixed"
the parameter names where possible. For endpoints that no longer exist,
the function returns the API error message.

Replace "YOUR_API_KEY_HERE" with your actual API key.

Note: Some endpoints (like shots, market value, timeline, video, player form,
team streaks, etc.) are not available in API‑Football v3. In those cases, the functions
will return the API error message.
"""

import requests

API_BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",  # Replace with your actual API key
    "x-apisports-host": "v3.football.api-sports.io"
}


# 1. Fetch fixtures by date.
def fetch_fixtures_by_date(date_str, league_id, season):
    """
    Fetch fixtures for a specific date.
    Endpoint: /fixtures?date={date_str}&league={league_id}&season={season}
    """
    url = f"{API_BASE_URL}/fixtures?date={date_str}&league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 2. Fetch fixture details.
def fetch_fixture_details(fixture_id):
    """
    Fetch detailed information for a given fixture.
    Endpoint: /fixtures?id={fixture_id}
    """
    url = f"{API_BASE_URL}/fixtures?id={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 3. Fetch all teams in a league.
def fetch_teams(league_id, season):
    """
    Fetch all teams for a given league and season.
    Endpoint: /teams?league={league_id}&season={season}
    """
    url = f"{API_BASE_URL}/teams?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 4. Fetch team details.
def fetch_team_details(team_id, season):
    """
    Fetch details for a given team.
    Endpoint: /teams?id={team_id}&season={season}
    """
    url = f"{API_BASE_URL}/teams?id={team_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 5. Fetch team standings.
def fetch_team_standings(league_id, season):
    """
    Fetch league standings for a given league and season.
    Endpoint: /standings?league={league_id}&season={season}
    """
    url = f"{API_BASE_URL}/standings?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 6. Fetch team statistics.
def fetch_team_statistics(team_id, season):
    """
    Fetch statistics for a team.
    Endpoint: /teams/statistics?team={team_id}&season={season}
    """
    url = f"{API_BASE_URL}/teams/statistics?team={team_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 7. Fetch team form.
def fetch_team_form(team_id, season):
    """
    Fetch recent form for a team.
    Endpoint: /fixtures?team={team_id}&season={season}&last=5
    """
    url = f"{API_BASE_URL}/fixtures?team={team_id}&season={season}&last=5"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 8. Fetch team home/away statistics.
def fetch_team_home_away_stats(team_id, season):
    """
    Fetch home/away statistics for a team.
    Use the same endpoint as fetch_team_statistics; caller must parse home/away.
    """
    return fetch_team_statistics(team_id, season)


# 9. Fetch team lineups.
def fetch_team_lineups(fixture_id):
    """
    Fetch lineups for a given fixture.
    Endpoint: /fixtures/lineups?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 10. Fetch team injuries.
def fetch_team_injuries(team_id, season):
    """
    Fetch injuries for a team.
    Endpoint: /injuries?team={team_id}&season={season}
    """
    url = f"{API_BASE_URL}/injuries?team={team_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 11. Fetch player details.
def fetch_player_details(player_id, season):
    """
    Fetch details for a specific player.
    Use endpoint: /players?id={player_id}&season={season}
    """
    url = f"{API_BASE_URL}/players?id={player_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 12. Fetch player statistics.
def fetch_player_statistics(player_id, season):
    """
    Fetch statistics for a specific player.
    Use endpoint: /players?id={player_id}&season={season}
    Note: The error "The Player field do not exist" is resolved by using 'id' instead.
    """
    url = f"{API_BASE_URL}/players?id={player_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 13. Fetch player shot statistics.
def fetch_player_shots(player_id, season):
    """
    (Not available: The /players/shots endpoint does not exist.)
    Returns a message indicating this endpoint is not available.
    """
    return {"error": "The players/shots endpoint does not exist in API-Football v3."}


# 14. Fetch player goal statistics.
def fetch_player_goals(player_id, season):
    """
    Fetch player goal statistics.
    Use the same endpoint as fetch_player_statistics.
    Caller should extract 'goals' field from the response.
    """
    return fetch_player_statistics(player_id, season)


# 15. Fetch player assist statistics.
def fetch_player_assists(player_id, season):
    """
    Fetch player assist statistics.
    Use the same endpoint as fetch_player_statistics.
    Caller should extract 'assists' field from the response.
    """
    return fetch_player_statistics(player_id, season)


# 16. Fetch player rating.
def fetch_player_rating(player_id, season):
    """
    Fetch player rating.
    Use the same endpoint as fetch_player_statistics.
    Caller should extract 'games.rating' from the response.
    """
    return fetch_player_statistics(player_id, season)


# 17. Fetch player market value.
def fetch_player_market_value(player_id, season):
    """
    (Not available: The players/market_value endpoint does not exist.)
    """
    return {"error": "The players/market_value endpoint does not exist in API-Football v3."}


# 18. Fetch fixture odds.
def fetch_match_odds(fixture_id):
    """
    Fetch odds for a given fixture.
    Endpoint: /odds?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 19. Fetch live match data.
def fetch_live_match_data(fixture_id):
    """
    Fetch live data for a fixture.
    Endpoint: /fixtures?id={fixture_id} 
    (If live data is available.)
    """
    url = f"{API_BASE_URL}/fixtures?id={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 20. Fetch head-to-head history.
def fetch_h2h_history(team1_id, team2_id, season):
    """
    Fetch head-to-head history for two teams.
    Endpoint: /fixtures/headtohead?h2h={team1_id}-{team2_id}&season={season}
    """
    url = f"{API_BASE_URL}/fixtures/headtohead?h2h={team1_id}-{team2_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 21. Fetch head-to-head summary.
def fetch_head_to_head(team1_id, team2_id):
    """
    Fetch a head-to-head summary for two teams.
    Endpoint: /fixtures/headtohead?h2h={team1_id}-{team2_id}
    """
    url = f"{API_BASE_URL}/fixtures/headtohead?h2h={team1_id}-{team2_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 22. Fetch fixture predictions.
def fetch_fixture_predictions(fixture_id):
    """
    Fetch predictions for a fixture.
    Endpoint: /predictions?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 23. Fetch fixture statistics.
def fetch_fixture_statistics(fixture_id):
    """
    Fetch statistics for a fixture.
    Endpoint: /fixtures/statistics?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/fixtures/statistics?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 24. Fetch live statistics.
def fetch_live_statistics(fixture_id):
    """
    Fetch live statistics for a fixture.
    Use the same endpoint as fixture statistics.
    """
    return fetch_fixture_statistics(fixture_id)


# 25. Fetch match events.
def fetch_match_events(fixture_id):
    """
    Fetch match events (goals, cards, substitutions, etc.) for a fixture.
    Endpoint: /fixtures/events?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/fixtures/events?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 26. Fetch match timeline.
def fetch_match_timeline(fixture_id):
    """
    (Not available: The fixtures/timeline endpoint does not exist.)
    """
    return {"error": "The fixtures/timeline endpoint does not exist in API-Football v3."}


# 27. Fetch corners data.
def fetch_corners(fixture_id):
    """
    Fetch corner statistics for a fixture.
    Use fixture statistics endpoint and extract corner info.
    """
    stats = fetch_fixture_statistics(fixture_id)
    return stats  # Caller must parse corner data


# 28. Fetch fouls data.
def fetch_fouls(fixture_id):
    """
    Fetch foul statistics for a fixture.
    Use fixture statistics endpoint and extract foul info.
    """
    stats = fetch_fixture_statistics(fixture_id)
    return stats  # Caller must parse fouls data


# 29. Fetch cards data.
def fetch_cards(fixture_id):
    """
    Fetch card statistics (yellow/red) for a fixture.
    Use fixture statistics endpoint and extract card info.
    """
    stats = fetch_fixture_statistics(fixture_id)
    return stats  # Caller must parse cards data


# 30. Fetch penalties data.
def fetch_penalties(fixture_id):
    """
    Fetch penalty statistics for a fixture.
    Use fixture statistics endpoint and extract penalty info.
    """
    stats = fetch_fixture_statistics(fixture_id)
    return stats  # Caller must parse penalty info


# 31. Fetch substitutions data.
def fetch_substitutions(fixture_id):
    """
    Fetch substitution data for a fixture.
    Use fixture events endpoint and filter for substitution events.
    """
    events = fetch_match_events(fixture_id)
    return events  # Caller must filter substitution events


# 32. Fetch referee data.
def fetch_referee_data(fixture_id):
    """
    Fetch referee information for a fixture.
    Use fixture details and extract referee info.
    """
    details = fetch_fixture_details(fixture_id)
    return details  # Caller must extract referee info


# 33. Fetch match attendance.
def fetch_match_attendance(fixture_id):
    """
    Fetch attendance data for a fixture.
    Use fixture details and extract attendance.
    """
    details = fetch_fixture_details(fixture_id)
    return details  # Caller must extract attendance info


# 34. Fetch weather for fixture.
def fetch_weather(fixture_id):
    """
    Fetch weather data for a fixture.
    (If not provided by API‑Football, this may require an external API.)
    """
    details = fetch_fixture_details(fixture_id)
    return details  # Caller must extract weather info if available


# 35. Fetch live lineups.
def fetch_live_lineups(fixture_id):
    """
    Fetch live lineups for a fixture.
    Use the same endpoint as fetch_team_lineups.
    """
    return fetch_team_lineups(fixture_id)


# 36. Fetch match video highlights.
def fetch_match_video_highlights(fixture_id):
    """
    (Not available: The fixtures/video endpoint does not exist.)
    """
    return {"error": "The fixtures/video endpoint does not exist in API-Football v3."}


# 37. Fetch team transfers.
def fetch_team_transfers(team_id, season):
    """
    Fetch transfers for a team.
    Endpoint: /transfers?team={team_id} (season parameter may not be supported)
    """
    url = f"{API_BASE_URL}/transfers?team={team_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 38. Fetch player transfers.
def fetch_player_transfers(player_id):
    """
    Fetch transfers for a player.
    Endpoint: /transfers?player={player_id}
    """
    url = f"{API_BASE_URL}/transfers?player={player_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 39. Fetch team budget.
def fetch_team_budget(team_id, season):
    """
    (Not available: The teams/budget endpoint does not exist.)
    """
    return {"error": "The teams/budget endpoint does not exist in API-Football v3."}


# 40. Fetch competition info.
def fetch_competition_info(league_id, season):
    """
    Fetch competition information.
    Endpoint: /leagues?league={league_id}&season={season}
    (Some fields may differ; if error, try without season parameter.)
    """
    url = f"{API_BASE_URL}/leagues?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 41. Fetch league table.
def fetch_league_table(league_id, season):
    """
    Fetch the league table.
    Endpoint: /standings?league={league_id}&season={season}
    """
    url = f"{API_BASE_URL}/standings?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 42. Fetch season statistics.
def fetch_season_statistics(league_id, season):
    """
    (Not available: The statistics endpoint as used previously does not exist.)
    """
    return {"error": "The statistics endpoint does not exist in API-Football v3."}


# 43. Fetch player form.
def fetch_player_form(player_id, season):
    """
    (Not available: The players/form endpoint does not exist.)
    """
    return {"error": "The players/form endpoint does not exist in API-Football v3."}


# 44. Fetch team streaks.
def fetch_team_streaks(team_id, season):
    """
    (Not available: The teams/streaks endpoint does not exist.)
    """
    return {"error": "The teams/streaks endpoint does not exist in API-Football v3."}


# 45. Fetch live odds.
def fetch_live_odds(fixture_id):
    """
    Fetch live odds for a fixture.
    Endpoint: /odds/live?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/odds/live?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 46. Fetch odds.
def fetch_odds(fixture_id):
    """
    Fetch odds for a fixture.
    Endpoint: /odds?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/odds?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 47. Fetch match referee.
def fetch_match_referee(fixture_id):
    """
    Fetch referee information for a fixture.
    (Extract from fixture details.)
    """
    details = fetch_fixture_details(fixture_id)
    return details  # Caller extracts referee info


# 48. Fetch player cards.
def fetch_player_cards(player_id, season):
    """
    Fetch card data for a player.
    Use endpoint: /players?id={player_id}&season={season} and extract cards info.
    """
    data = fetch_player_statistics(player_id, season)
    return data  # Caller extracts card details


# 49. Fetch team cards.
def fetch_team_cards(team_id, season):
    """
    Fetch card data for a team.
    Use endpoint: /teams/statistics?team={team_id}&season={season} and extract card info.
    """
    data = fetch_team_statistics(team_id, season)
    return data  # Caller extracts card details


# -----------------------------
# Main block: Sample calls for demonstration.
# -----------------------------
if __name__ == "__main__":
    sample_date = "2025-04-05"
    sample_league_id = 39
    sample_season = 2024
    sample_fixture_id = 1208318
    sample_team_id = 33
    sample_player_id = 2371  # e.g., a famous player if available


    print("\n6. Team statistics:")
    print(fetch_team_statistics(sample_team_id, sample_season))
    

    print("\n11. Player details:")
    print(fetch_player_details(sample_player_id, sample_season))
    
    print("\n12. Player statistics:")
    print(fetch_player_statistics(sample_player_id, sample_season))
    
    print("\n13. Player shot statistics:")
    print(fetch_player_shots(sample_player_id, sample_season))
    
    print("\n14. Player goal statistics:")
    print(fetch_player_goals(sample_player_id, sample_season))
    
    print("\n15. Player assist statistics:")
    print(fetch_player_assists(sample_player_id, sample_season))
    
    print("\n16. Player rating:")
    print(fetch_player_rating(sample_player_id, sample_season))
