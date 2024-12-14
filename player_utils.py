import asyncio
from understat import Understat
import aiohttp

async def fetch_goalkeeper_stats(team_name, season, num_matches=None):
    """
    Fetch goalkeeper stats for a specific team and season.

    Args:
        team_name (str): Name of the team (e.g., "Liverpool").
        season (str): The season (e.g., "2023").
        num_matches (int, optional): Number of recent matches to fetch. If None, fetches all matches.

    Returns:
        dict: Goalkeeper stats containing name, ID, average goals conceded, and average opponent xG.
    """
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)

        # Fetch team results
        team_results = await understat.get_team_results(team_name=team_name, season=season)

        # Limit to last 'num_matches' if specified
        if num_matches:
            team_results = team_results[-num_matches:]

        gk_stats = {}
        total_matches = {}

        for match in team_results:
            match_id = match['id']

            # Determine if team is the home team
            is_home = match['h']['title'] == team_name

            # Goals conceded and xG from opponents
            goals_conceded = int(match['goals']['a']) if is_home else int(match['goals']['h'])
            opponent_xg = float(match['xG']['a']) if is_home else float(match['xG']['h'])

            # Fetch detailed player data for the match
            match_players = await understat.get_match_players(match_id)

            # Extract players for the relevant team
            team_players = match_players['h'] if is_home else match_players['a']

            # Extract goalkeeper info
            gk_data = next(
                (player for player in team_players.values() if player['position'] == 'GK'),
                {"player": "Unknown", "player_id": "Unknown"}
            )
            goalkeeper = gk_data['player']
            goalkeeper_id = gk_data['player_id']

            # Update stats for the goalkeeper
            if goalkeeper_id not in gk_stats:
                gk_stats[goalkeeper_id] = {"name": goalkeeper, "goals_conceded": 0, "opponent_xG": 0}
                total_matches[goalkeeper_id] = 0

            gk_stats[goalkeeper_id]["goals_conceded"] += goals_conceded
            gk_stats[goalkeeper_id]["opponent_xG"] += opponent_xg
            total_matches[goalkeeper_id] += 1

        # Calculate averages
        for gk_id, stats in gk_stats.items():
            stats["average_goals_conceded"] = stats["goals_conceded"] / total_matches[gk_id]
            stats["average_opponent_xG"] = stats["opponent_xG"] / total_matches[gk_id]

        return gk_stats


def get_goalkeeper_stats(team_name, season, num_matches=None):
    """
    Wrapper function to fetch goalkeeper stats synchronously.

    Args:
        team_name (str): Name of the team (e.g., "Liverpool").
        season (str): The season (e.g., "2023").
        num_matches (int, optional): Number of recent matches to fetch. If None, fetches all matches.

    Returns:
        dict: Goalkeeper stats containing name, ID, average goals conceded, and average opponent xG.
    """
    return asyncio.run(fetch_goalkeeper_stats(team_name, season, num_matches))
