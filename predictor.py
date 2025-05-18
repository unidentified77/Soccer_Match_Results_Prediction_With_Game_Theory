# predictor.py
import sys
import requests
import pandas as pd
import numpy as np
from math import exp, factorial
from datetime import date, timedelta, datetime

from team_power import Team, fill_all_stats
from tactics import determine_team_formation, determine_team_play_style
from gametheory import synergy_from_formation_style, calculate_combination_percentages
from api_football_features import (
    fetch_injuries,
    fetch_lineup_strength,
    fetch_odds,
    fetch_team_standing,
    fetch_rest_days
)
from utils import UnderstatClient

BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-apisports-key": "078dfd2522b94892b4675b57bd810999",
    "x-apisports-host": "v3.football.api-sports.io"
}
LEAGUE_ID = 39
SEASON    = 2024

POISSON_SCALE = 0.25
# Lower synergy weight or let synergy remain the same; you can do more advanced synergy logic if you want.

DEBUG = True
def debug_print(msg):
    if DEBUG:
        print(msg)

def load_history(filename="history_df.xlsx"):
    try:
        return pd.read_excel(filename)
    except Exception as e:
        print(f"Error loading history data: {e}")
        return pd.DataFrame()

def fetch_recent_fixtures_20_days(league_id=LEAGUE_ID, season=SEASON):
    # same as before
    end_date = date.today()
    start_date = end_date - timedelta(days=20)
    from_str = start_date.isoformat()
    to_str   = end_date.isoformat()
    url = (f"{BASE_URL}/fixtures?league={league_id}&season={season}"
           f"&from={from_str}&to={to_str}")
    debug_print(f"[fetch_recent_fixtures_20_days] GET {url}")
    resp = requests.get(url, headers=API_HEADERS)
    data = resp.json()
    # parse fixtures...
    fixtures_list = []
    if data.get("response"):
        for item in data["response"]:
            fix = item["fixture"]
            teams = item["teams"]
            home  = teams["home"]
            away  = teams["away"]
            fixture_id  = fix["id"]
            fixture_dt  = fix["date"]
            status_short = fix["status"]["short"]
            fdict = {
                "fixture_id": fixture_id,
                "date": fixture_dt,
                "status": status_short,
                "home_team_id": home["id"],
                "home_team_name": home["name"],
                "away_team_id": away["id"],
                "away_team_name": away["name"]
            }
            fixtures_list.append(fdict)
    return fixtures_list

def adjust_team_power_with_bonus(team: Team, bonus: float) -> float:
    if not hasattr(team, "base_strength"):
        return bonus
    return team.base_strength + bonus

def poisson_pmf(lmbda, k):
    return exp(-lmbda) * (lmbda**k) / factorial(k)

def predict_score_poisson(lam_home: float, lam_away: float, max_goals: int = 6):
    best_prob = -1
    best_h, best_a = 0, 0
    for h in range(max_goals+1):
        p_h = poisson_pmf(lam_home, h)
        for a in range(max_goals+1):
            p_a = poisson_pmf(lam_away, a)
            joint = p_h * p_a
            if joint > best_prob:
                best_prob = joint
                best_h, best_a = h, a
    return best_h, best_a

def main():
    recent = fetch_recent_fixtures_20_days()
    if not recent:
        print("No fixtures found in the last 20 days.")
        sys.exit(0)

    history_df = load_history("history_df.xlsx")
    if history_df.empty:
        print("Warning: 'history_df.xlsx' not found or empty.")

    # filter for completed
    completed_matches = [f for f in recent if f["status"] in ("FT","AET","PEN")]
    if not completed_matches:
        print("No completed fixtures found in last 20 days.")
        sys.exit(0)

    print(f"\n=== Found {len(completed_matches)} completed EPL fixtures in the last 20 days ===\n")

    # CHANGED: We'll lower the scale factor from 0.35 to 0.25
    POISSON_SCALE = 0.25

    with UnderstatClient() as understat:
        for i, fix in enumerate(completed_matches, start=1):
            fixture_id = fix["fixture_id"]
            fixture_date = fix["date"]
            home_team_id = fix["home_team_id"]
            home_team_name = fix["home_team_name"]
            away_team_id = fix["away_team_id"]
            away_team_name = fix["away_team_name"]

            print(f"\n[{i}/{len(completed_matches)}] FixtureID={fixture_id}, {home_team_name} vs {away_team_name}, date={fixture_date}, status={fix['status']}")

            # Create Team objects
            home_team = Team(name=home_team_name, short_title=home_team_name[:3].upper())
            away_team = Team(name=away_team_name, short_title=away_team_name[:3].upper())

            # fill stats
            fill_all_stats(home_team, current_season=str(SEASON), last_season=str(SEASON-1), all_seasons=[str(SEASON-1), str(SEASON)], understat=understat)
            fill_all_stats(away_team, current_season=str(SEASON), last_season=str(SEASON-1), all_seasons=[str(SEASON-1), str(SEASON)], understat=understat)

            # formation & style
            home_team.formation = determine_team_formation(home_team)
            home_team.style = determine_team_play_style(home_team)
            away_team.formation = determine_team_formation(away_team)
            away_team.style = determine_team_play_style(away_team)

            home_team.base_strength = home_team.calculate_team_strength()
            away_team.base_strength = away_team.calculate_team_strength()

            # synergy
            formA = home_team.last_match_formation or home_team.formation
            styA  = home_team.style
            formB = away_team.last_match_formation or away_team.formation
            styB  = away_team.style
            bonusA, bonusB = synergy_from_formation_style(formA, styA, formB, styB, history_df)
            home_strength_adj = adjust_team_power_with_bonus(home_team, bonusA)
            away_strength_adj = adjust_team_power_with_bonus(away_team, bonusB)

            # CHANGED: Add a small home advantage
            # e.g. +1.0 to home strength
            home_strength_adj += 1.0

            # injuries 
            injuries_home = fetch_injuries(fixture_id, home_team_id, SEASON)
            injuries_away = fetch_injuries(fixture_id, away_team_id, SEASON)
            home_strength_adj -= 0.2 * len(injuries_home)
            away_strength_adj -= 0.2 * len(injuries_away)

            # lineup
            lineup_data = fetch_lineup_strength(fixture_id)
            if lineup_data and isinstance(lineup_data.get("strength_score"), dict):
                top_home = lineup_data["strength_score"].get(home_team_name, 0)
                top_away = lineup_data["strength_score"].get(away_team_name, 0)
                home_strength_adj += 0.1 * top_home
                away_strength_adj += 0.1 * top_away

            # standings
            home_standing = fetch_team_standing(home_team_id, league_id=LEAGUE_ID, season=SEASON)
            away_standing = fetch_team_standing(away_team_id, league_id=LEAGUE_ID, season=SEASON)

            # CHANGED: Fix rest-days logic so the "from" date is earlier
            # We'll parse fixture_date, do from= "2024-07-01" (for example) to that fixture_date
            def fixed_rest_days(team_id, fix_date_str):
                try:
                    dt = datetime.fromisoformat(fix_date_str.replace("Z","").split("+")[0])
                    from_s = "2024-07-01"  # or season start
                    to_s = dt.strftime("%Y-%m-%d")
                    url_rd = f"{BASE_URL}/fixtures?team={team_id}&from={from_s}&to={to_s}&season={dt.year}&status=FT"
                    r = requests.get(url_rd, headers=API_HEADERS)
                    j = r.json()
                    if j.get("response"):
                        past = []
                        for fi in j["response"]:
                            # check date
                            fdt_str = fi["fixture"]["date"]
                            fdt = datetime.fromisoformat(fdt_str.replace("Z","").split("+")[0])
                            if fdt < dt:
                                past.append(fi)
                        past.sort(key=lambda x: x["fixture"]["date"], reverse=True)
                        if past:
                            last_dt_str = past[0]["fixture"]["date"]
                            last_dt = datetime.fromisoformat(last_dt_str.replace("Z","").split("+")[0])
                            delta = dt - last_dt
                            return delta.days
                except:
                    pass
                return None

            home_rest = fixed_rest_days(home_team_id, fixture_date)
            away_rest = fixed_rest_days(away_team_id, fixture_date)

            if home_rest is not None and home_rest < 3:
                home_strength_adj -= 0.2
            if away_rest is not None and away_rest < 3:
                away_strength_adj -= 0.2

            # final
            home_team.final_strength = max(home_strength_adj, 0.0)
            away_team.final_strength = max(away_strength_adj, 0.0)

            lam_home = POISSON_SCALE * home_team.final_strength
            lam_away = POISSON_SCALE * away_team.final_strength
            phg, pag = predict_score_poisson(lam_home, lam_away, max_goals=6)

            if phg > pag:
                predicted_outcome = "Home Win"
            elif phg < pag:
                predicted_outcome = "Away Win"
            else:
                predicted_outcome = "Draw"

            # actual final
            actual_h, actual_a = None, None
            try:
                uf = f"{BASE_URL}/fixtures?id={fixture_id}"
                r2 = requests.get(uf, headers=API_HEADERS).json()
                if r2.get("response"):
                    gls = r2["response"][0]["goals"]
                    actual_h, actual_a = gls["home"], gls["away"]
            except:
                pass

            # odds
            odds_data = fetch_odds(fixture_id)

            # print
            print("-------------------------------------")
            print(f"Home: {home_team_name}, Str={home_team.final_strength:.2f}, Formation={home_team.formation}, Style={home_team.style}, RestDays={home_rest}")
            print(f"Away: {away_team_name}, Str={away_team.final_strength:.2f}, Formation={away_team.formation}, Style={away_team.style}, RestDays={away_rest}")
            print(f"Poisson λ => Home={lam_home:.2f}, Away={lam_away:.2f}")
            print(f"Predicted Score => {phg}-{pag} => {predicted_outcome}")
            if actual_h is not None and actual_a is not None:
                print(f"Actual Score    => {actual_h}-{actual_a}")
            if odds_data:
                print(f"Odds => {odds_data}")
            print("-------------------------------------")

    print("\n=== Done with improved predictor ===")

if __name__ == "__main__":
    main()