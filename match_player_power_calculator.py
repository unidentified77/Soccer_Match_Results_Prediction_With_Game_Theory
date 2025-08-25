#!/usr/bin/env python3
"""
match_player_power_calculator.py

This module calculates an advanced power score for each player in a given fixture by
combining data from Understat and API‑Football. Understat provides detailed per‑player stats 
(e.g. goals, xG, assists, xA, shots, key passes, yellow/red cards, npg, npxG, xGChain, xGBuildup, games, minutes,
tackles, duels, dribbles, interceptions), and API‑Football supplies lineup and injury information.
Because the two APIs use different IDs, players are merged by matching their normalized names
(using ASCII normalization).

For each player we compute three components:
  • SC (Current Season Score): weighted per‑game averages from the current season.
  • RC (Recent Form Score): weighted per‑match averages from the last 5 matches (amplified).
  • CC (Career Score): weighted per‑game averages aggregated over the last 5 seasons.
  
Final Power = ALPHA * RC + BETA * SC + GAMMA * CC

A player is flagged as injured if an injury record for the selected fixture is found
via API‑Football. (Even if injured, their power is calculated but they are marked "Injured".)

The script saves the complete roster (with statuses and individual power scores) as well as the total power
of the first eleven for each team to an Excel file.
It also prints the normalized JSON used in calculating recent and career stats.
"""

import json
import logging
import unicodedata
from statistics import mean
import pandas as pd

# --- IMPORT UNDERSTAT FUNCTIONS ---
from understat_fetch_functions import (
    UnderstatClient,
    fetch_player_stats,
    fetch_player_career_stats,
    fetch_recent_stats
)

# --- IMPORT API‑FOOTBALL FUNCTIONS ---
from dataFetch.apiSportsFetchFunctions import (
    fetch_team_lineups,
    fetch_player_injuries,
    fetch_player_statistics
)

# --- BLENDING WEIGHTS & MULTIPLIER ---
ALPHA = 0.5   # Weight for Recent Form
BETA  = 0.3   # Weight for Current Season
GAMMA = 0.2   # Weight for Career
RECENT_MULTIPLIER = 1.5  # Amplification factor for recent form

# --- POSITION WEIGHTS ---
POSITION_WEIGHTS = {
    "F": {
        "goals": 5.0,
        "xG": 3.0,
        "assists": 2.0,
        "xA": 1.5,
        "shots": 1.0,
        "key_passes": 1.5,
        "npxG": 2.0,
        "xGChain": 1.0,
        "xGBuildup": 0.5,
        "yellow": -1.0,
        "red": -3.0,
        "tackles": 0.0,
        "duels": 0.0,
        "dribbles": 1.0,
        "interceptions": 0.0
    },
    "M": {
        "goals": 3.0,
        "xG": 3.0,
        "assists": 3.0,
        "xA": 2.5,
        "shots": 0.8,
        "key_passes": 2.0,
        "npxG": 1.5,
        "xGChain": 1.0,
        "xGBuildup": 1.0,
        "yellow": -0.5,
        "red": -2.0,
        "tackles": 0.5,
        "duels": 0.5,
        "dribbles": 0.5,
        "interceptions": 0.5
    },
    "D": {
        "goals": 2.0,
        "xG": 1.0,
        "assists": 1.0,
        "xA": 0.5,
        "shots": 0.5,
        "key_passes": 1.0,
        "npxG": 1.0,
        "xGChain": 0.5,
        "xGBuildup": 0.5,
        "yellow": -1.0,
        "red": -3.0,
        "tackles": 1.0,
        "duels": 0.8,
        "dribbles": 0.2,
        "interceptions": 1.0
    },
    "G": {
        "saves": 5.0,
        "clean_sheet": 3.0,
        "yellow": -0.5,
        "red": -3.0
    }
}

# --- SET UP LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- HELPER FUNCTIONS ---
def ascii_normalize(text: str) -> str:
    """Normalize text to ASCII, lowercased and stripped."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower().strip()

def normalize_name(name: str) -> str:
    return ascii_normalize(name)

def get_position_category(pos_str: str) -> str:
    pos = pos_str.upper()
    if "GK" in pos or pos.startswith("G"):
        return "G"
    elif "D" in pos:
        return "D"
    elif "F" in pos:
        return "F"
    else:
        return "M"

def compute_component_score_full(stats: dict, weights: dict) -> float:
    """Compute weighted sum over all metrics in stats using weights."""
    score = 0.0
    for metric, weight in weights.items():
        try:
            value = float(stats.get(metric, 0))
        except (TypeError, ValueError):
            value = 0.0
        score += value * weight
    return score

def compute_gk_power(stats: dict, weights: dict) -> float:
    """Compute goalkeeper power using 'saves' and 'clean_sheet'."""
    try:
        saves = float(stats.get("saves", 0))
    except:
        saves = 0.0
    try:
        cs = float(stats.get("clean_sheet", 0))
    except:
        cs = 0.0
    return saves * weights.get("saves", 0) + cs * weights.get("clean_sheet", 0)

def normalize_understat_record(rec: dict) -> dict:
    """
    Converts a raw Understat record into normalized per-game averages.
    Expects keys: games, goals, xG, assists, xA, shots, key_passes, yellow_cards, red_cards,
    npxG, xGChain, xGBuildup, npg.
    For goalkeepers, includes saves and clean_sheet.
    Defensive metrics not provided by Understat are set to 0.
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
        "npxG": 0.0,  # will compute below
        "xGChain": float(rec.get("xGChain", 0)) / games,
        "xGBuildup": float(rec.get("xGBuildup", 0)) / games,
        "npg": float(rec.get("npg", 0)) / games,
        "tackles": 0.0,
        "duels": 0.0,
        "dribbles": 0.0,
        "interceptions": 0.0
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

def aggregate_stats(records: list) -> dict:
    if not records:
        return {}
    metrics = records[0].keys()
    return {m: mean(rec.get(m, 0) for rec in records) for m in metrics}

# --- FALLBACK FUNCTIONS USING MATCH-BY-MATCH (Understat) ---
def fallback_recent_stats_hard(team: str, player_name: str, season: str, last_n: int = 5) -> dict:
    """Fallback: Calculate recent stats by scanning the last_n matches of the team."""
    recent_records = []
    with UnderstatClient() as understat:
        matches = understat.team(team).get_match_data(season=season)
        for match in reversed(matches):
            match_id = match.get("id")
            if not match_id:
                continue
            try:
                roster = understat.match(match_id).get_roster_data()
            except Exception:
                continue
            for side in ["h", "a"]:
                for pid, pstats in roster.get(side, {}).items():
                    candidate = pstats.get("player") or pstats.get("player_name", "")
                    if normalize_name(candidate) == normalize_name(player_name):
                        recent_records.append(normalize_understat_record(pstats))
                        break
            if len(recent_records) >= last_n:
                break
    return aggregate_stats(recent_records)

def fallback_career_stats_hard(team: str, player_name: str, career_seasons: list, max_matches_per_season: int = 10) -> dict:
    """Fallback: Calculate career stats by scanning up to max_matches_per_season per season."""
    career_records = []
    with UnderstatClient() as understat:
        for s in career_seasons:
            matches = understat.team(team).get_match_data(season=s)
            count = 0
            for match in matches:
                if count >= max_matches_per_season:
                    break
                match_id = match.get("id")
                if not match_id:
                    continue
                try:
                    roster = understat.match(match_id).get_roster_data()
                except Exception:
                    continue
                found = False
                for side in ["h", "a"]:
                    for pid, pstats in roster.get(side, {}).items():
                        candidate = pstats.get("player") or pstats.get("player_name", "")
                        if normalize_name(candidate) == normalize_name(player_name):
                            career_records.append(normalize_understat_record(pstats))
                            found = True
                            count += 1
                            break
                    if found:
                        break
    return aggregate_stats(career_records)

# --- FALLBACK FUNCTIONS USING API‑FOOTBALL FOR DEFENSIVE METRICS ---
def fallback_api_recent_stats(api_player_id: str, season: str) -> dict:
    data = fetch_player_statistics(api_player_id, season)
    if "response" in data and data["response"]:
        player_obj = data["response"][0]
        if "statistics" in player_obj and len(player_obj["statistics"]) > 0:
            stats = player_obj["statistics"][0]
            tackles = (stats.get("tackles") or {}).get("total", 0)
            duels = (stats.get("duels") or {}).get("total", 0)
            dribbles = (stats.get("dribbles") or {}).get("attempts", 0)
            interceptions = (stats.get("tackles") or {}).get("interceptions", 0)
            return {
                "tackles": float(tackles or 0),
                "duels": float(duels or 0),
                "dribbles": float(dribbles or 0),
                "interceptions": float(interceptions or 0)
            }
    return {}

def fallback_api_career_stats(api_player_id: str, career_seasons: list) -> dict:
    records = []
    for s in career_seasons:
        rec = fallback_api_recent_stats(api_player_id, s)
        if rec:
            records.append(rec)
    if records:
        return {
            "tackles": mean(r["tackles"] for r in records),
            "duels": mean(r["duels"] for r in records),
            "dribbles": mean(r["dribbles"] for r in records),
            "interceptions": mean(r["interceptions"] for r in records)
        }
    return {}

def merge_defensive_stats(understat_stats: dict, api_stats: dict) -> dict:
    """Merge defensive metrics from API‑Football into Understat stats."""
    for key in ["tackles", "duels", "dribbles", "interceptions"]:
        if key in api_stats:
            understat_stats[key] = api_stats[key]
    return understat_stats

# --- COMBINE UNDERSTAT DATA (with API defensive metrics merged) ---
def combine_player_understat_data(player_name: str, team: str, current_season: str, career_seasons: list, api_player_id: str = None) -> dict:
    current = {}
    recent = {}
    career = {}
    
    with UnderstatClient() as understat:
        # CURRENT SEASON from Understat.
        team_players = understat.team(team).get_player_data(season=current_season)
        for rec in team_players:
            candidate = rec.get("player") or rec.get("player_name", "")
            if normalize_name(candidate) == normalize_name(player_name):
                current = normalize_understat_record(rec)
                break
        
        # RECENT from Understat.
        rec_list = fetch_recent_stats(understat, player_name, team, current_season, last_n=5)
        normalized_recent = [normalize_understat_record(r) for r in rec_list]
        recent = aggregate_stats(normalized_recent)
        if not recent:
            recent = fallback_recent_stats_hard(team, player_name, current_season, last_n=5)
        # Merge API‑Football defensive metrics if available.
        if api_player_id and api_player_id.isdigit():
            api_recent = fallback_api_recent_stats(api_player_id, current_season)
            recent = merge_defensive_stats(recent, api_recent)
        
        # CAREER from Understat.
        career_records = []
        career_data = fetch_player_career_stats(player_name, career_seasons)
        for s in career_seasons:
            season_recs = career_data.get("career_stats", {}).get(s, [])
            for rec in season_recs:
                candidate = rec.get("player") or rec.get("player_name", "")
                if normalize_name(candidate) == normalize_name(player_name):
                    career_records.append(normalize_understat_record(rec))
                    break
        career = aggregate_stats(career_records)
        if not career:
            career = fallback_career_stats_hard(team, player_name, career_seasons)
        if api_player_id and api_player_id.isdigit():
            api_career = fallback_api_career_stats(api_player_id, career_seasons)
            career = merge_defensive_stats(career, api_career)
    
    return {"current": current, "recent": recent, "career": career}

# --- COMPUTE PLAYER POWER (returns final power and injured flag) ---
def compute_player_power(player_name: str, team: str, position: str, current_season: str, career_seasons: list, fixture_id: str, api_player_id: str = None) -> tuple[float, bool]:
    pos_cat = get_position_category(position)
    weights = POSITION_WEIGHTS["G"] if pos_cat == "G" else POSITION_WEIGHTS.get(pos_cat, POSITION_WEIGHTS["M"])
    
    data = combine_player_understat_data(player_name, team, current_season, career_seasons, api_player_id)
    
    if pos_cat == "G":
        sc = compute_gk_power(data.get("current", {}), weights)
        cc = compute_gk_power(data.get("career", {}), weights)
        rc = RECENT_MULTIPLIER * compute_gk_power(data.get("recent", {}), weights)
    else:
        sc = compute_component_score_full(data.get("current", {}), weights)
        cc = compute_component_score_full(data.get("career", {}), weights)
        rc = RECENT_MULTIPLIER * compute_component_score_full(data.get("recent", {}), weights)
    
    print(f"\nData for {player_name} ({position}):")
    print("  Normalized Recent stats JSON:")
    print(json.dumps(data.get("recent", {}), indent=2))
    print("  Normalized Career stats JSON:")
    print(json.dumps(data.get("career", {}), indent=2))
    
    final_score = ALPHA * rc + BETA * sc + GAMMA * cc
    
    # Check injuries using API‑Football: mark as injured if an injury record for this fixture is found.
    injured = False
    if api_player_id and api_player_id.isdigit():
        inj_data = fetch_player_injuries(api_player_id, current_season)
        if "response" in inj_data and inj_data["response"]:
            for inj in inj_data["response"]:
                inj_fixture = inj.get("fixture", {}).get("id")
                if str(inj_fixture) == fixture_id:
                    injured = True
                    break
    return final_score, injured

# --- SAVE RESULTS TO EXCEL ---
def save_results_to_excel(results: dict, filename: str):
    """Save the final roster and total first eleven power per team to an Excel file."""
    rows = []
    totals = {}
    for side in results:
        first_eleven_power = sum(p["power"] for p in results[side]["first_eleven"])
        totals[side] = first_eleven_power
        for p in results[side]["all_players"]:
            rows.append({
                "Team": side.title(),
                "Player": p["name"],
                "Position": p["position"],
                "Power": p["power"],
                "Status": p["status"],
                "Role": p["role"]
            })
    df_lineup = pd.DataFrame(rows)
    df_totals = pd.DataFrame([{"Team": k.title(), "Total First Eleven Power": v} for k, v in totals.items()])
    with pd.ExcelWriter(filename) as writer:
        df_lineup.to_excel(writer, sheet_name="Lineups", index=False)
        df_totals.to_excel(writer, sheet_name="Totals", index=False)

# --- CALCULATE MATCH PLAYER POWERS WITH LINEUP ---
def calculate_match_player_powers(fixture_id: str, current_season: str, career_seasons: list) -> dict:
    lineup_data = fetch_team_lineups(fixture_id)
    if "response" not in lineup_data or len(lineup_data["response"]) < 2:
        logging.error("Incomplete lineup data; expected at least two teams.")
        return {}
    
    teams_power = {"home": [], "away": []}
    
    # Assume response order: [home_team, away_team]
    for side, lineup in zip(["home", "away"], lineup_data["response"]):
        team_name = lineup.get("team", {}).get("name", "Unknown")
        # Process starters.
        for starter in lineup.get("startXI", []):
            pinfo = starter.get("player", {})
            player_name = pinfo.get("name", "Unknown")
            position = pinfo.get("pos", "M")
            api_player_id = str(pinfo.get("id", ""))
            power, injured = compute_player_power(player_name, team_name, position, current_season, career_seasons, fixture_id, api_player_id)
            teams_power[side].append({
                "name": player_name,
                "position": position,
                "power": power,
                "injured": injured,
                "role": "Starter"
            })
        # Process substitutes.
        for sub in lineup.get("substitutes", []):
            pinfo = sub.get("player", {})
            player_name = pinfo.get("name", "Unknown")
            position = pinfo.get("pos", "M")
            api_player_id = str(pinfo.get("id", ""))
            power, injured = compute_player_power(player_name, team_name, position, current_season, career_seasons, fixture_id, api_player_id)
            teams_power[side].append({
                "name": player_name,
                "position": position,
                "power": power,
                "injured": injured,
                "role": "Substitute"
            })
    
    # Adjust lineups: For each team, mark starters; if a starter is injured, promote the best substitute.
    final_lineup = {"home": {"first_eleven": [], "all_players": []},
                    "away": {"first_eleven": [], "all_players": []}}
    
    for side in ["home", "away"]:
        starters = [p for p in teams_power[side] if p["role"] == "Starter"]
        subs = [p for p in teams_power[side] if p["role"] == "Substitute"]
        healthy_starters = [p for p in starters if not p["injured"]]
        needed = 11 - len(healthy_starters)
        promotable_subs = sorted([p for p in subs if not p["injured"]], key=lambda p: p["power"], reverse=True)
        promoted = promotable_subs[:needed] if needed > 0 else []
        for p in promoted:
            p["role"] = "Promoted Substitute"
        for p in teams_power[side]:
            if p["role"] == "Starter" and not p["injured"]:
                p["status"] = "First Eleven"
            elif p["role"] == "Starter" and p["injured"]:
                p["status"] = "Injured"
            elif p["role"] == "Promoted Substitute":
                p["status"] = "Promoted Substitute"
            else:
                p["status"] = "Subs"
        final_lineup[side]["first_eleven"] = healthy_starters + promoted
        final_lineup[side]["all_players"] = teams_power[side]
    
    return final_lineup

# --- MAIN ROUTINE ---
if __name__ == "__main__":
    fixture_id = input("Enter fixture id (from API-Sports): ").strip()
    current_season = "2024"
    career_seasons = ["2020", "2021", "2022", "2023", "2024"]
    
    player_powers = calculate_match_player_powers(fixture_id, current_season, career_seasons)
    if player_powers:
        print("\nPlayer Power Scores for the Match:")
        for side in ["home", "away"]:
            print(f"\n--- {side.upper()} TEAM ---")
            print("\nFirst Eleven:")
            for p in player_powers[side]["first_eleven"]:
                print(f"{p['name']:<25} (Pos: {p['position']}) -> Power: {p['power']:.2f}  Status: {p['status']}")
            print("\nAll Roster:")
            for p in player_powers[side]["all_players"]:
                print(f"{p['name']:<25} (Pos: {p['position']}) -> Power: {p['power']:.2f}  Status: {p['status']}")
        
        # Calculate total first eleven power per team.
        totals = {}
        for side in player_powers:
            totals[side] = sum(p["power"] for p in player_powers[side]["first_eleven"])
        print("\nTotal First Eleven Power:")
        for side in totals:
            print(f"{side.title()} Team: {totals[side]:.2f}")
        
        # Save results to Excel.
        save_results_to_excel(player_powers, "match_player_powers.xlsx")