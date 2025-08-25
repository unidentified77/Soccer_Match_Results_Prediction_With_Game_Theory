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

# 1. Fetch team lineups.
def fetch_team_lineups(fixture_id):
    """
    Fetch lineups for a given fixture.
    Endpoint: /fixtures/lineups?fixture={fixture_id}
    """
    url = f"{API_BASE_URL}/fixtures/lineups?fixture={fixture_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# 2. Fetch team injuries.
def fetch_team_injuries(team_id, season):
    """
    Fetch injuries for a team.
    Endpoint: /injuries?team={team_id}&season={season}
    """
    url = f"{API_BASE_URL}/injuries?team={team_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# 3. Fetch player statistics.
def fetch_player_statistics(player_id, season):
    """
    Fetch statistics for a specific player.
    Use endpoint: /players?id={player_id}&season={season}
    Note: The error "The Player field do not exist" is resolved by using 'id' instead.
    """
    url = f"{API_BASE_URL}/players?id={player_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# 4. Fetch player injuries.
def fetch_player_injuries(player_id, season):
    """
    Fetch injury data for a player.
    Endpoint: /injuries?player={player_id}&season={season}
    """
    url = f"{API_BASE_URL}/injuries?player={player_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    return response.json()