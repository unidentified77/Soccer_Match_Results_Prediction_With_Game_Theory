# gametheory.py

from utils import pd, np

DEBUG = True
def debug_print(msg):
    if DEBUG:
        print("[DEBUG]", msg)

def synergy_from_formation_style(formA, styA, formB, styB, history_df):
    # Normalize input strings
    norm_formA = formA.strip().lower() if formA else ""
    norm_styA  = styA.strip().lower() if styA else ""
    norm_formB = formB.strip().lower() if formB else ""
    norm_styB  = styB.strip().lower() if styB else ""

    debug_print(f"synergy_from_formation_style => (formA={norm_formA}, styA={norm_styA}, formB={norm_formB}, styB={norm_styB})")
    
    if history_df is None or history_df.empty:
        debug_print("  synergy => history_df is empty => 0,0")
        return (0.0, 0.0)

    # Create normalized columns for matching
    history_df["Formation_home_norm"] = history_df["Formation_home"].astype(str).str.strip().str.lower()
    history_df["style_home_norm"] = history_df["style_home"].astype(str).str.strip().str.lower()
    history_df["Formation_away_norm"] = history_df["Formation_away"].astype(str).str.strip().str.lower()
    history_df["style_away_norm"] = history_df["style_away"].astype(str).str.strip().str.lower()

    # Select rows where the match-up of formation and style appears (in either home/away order)
    sub = history_df.loc[
        (
            (history_df["Formation_home_norm"] == norm_formA) &
            (history_df["style_home_norm"] == norm_styA) &
            (history_df["Formation_away_norm"] == norm_formB) &
            (history_df["style_away_norm"] == norm_styB)
        )
        |
        (
            (history_df["Formation_home_norm"] == norm_formB) &
            (history_df["style_home_norm"] == norm_styB) &
            (history_df["Formation_away_norm"] == norm_formA) &
            (history_df["style_away_norm"] == norm_styA)
        )
    ]
    debug_print(f" synergy => found {len(sub)} matching rows in last_10 synergy check.")
    sub = sub.tail(10)
    if sub.empty:
        return (0.0, 0.0)

    a_bonus = 0.0
    b_bonus = 0.0
    for _, row in sub.iterrows():
        hg = row["goals_home"]
        ag = row["goals_away"]
        # Skip ties
        if hg == ag:
            continue
        if hg > ag:
            # Home win: bonus goes to the side that played with (formA, styA) as home
            if row["Formation_home_norm"] == norm_formA and row["style_home_norm"] == norm_styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3
        elif ag > hg:
            # Away win: bonus goes to the side that played with (formA, styA) as away
            if row["Formation_away_norm"] == norm_formA and row["style_away_norm"] == norm_styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3

    debug_print(f" synergy => a_bonus={a_bonus}, b_bonus={b_bonus}")
    return (a_bonus, b_bonus)


def calculate_combination_percentages(history_df, home_style, away_style):
    """
    Based on historical data, calculate winning percentages when a matchup
    with a specific home and away style occurs.
    Returns a dict with percentages for home win, draw, and away win.
    """
    sub = history_df.loc[
        (history_df["style_home"] == home_style) & (history_df["style_away"] == away_style)
    ]
    total_matches = len(sub)
    if total_matches == 0:
        return {"home_win": 0.0, "draw": 0.0, "away_win": 0.0}
    home_wins = len(sub[sub["goals_home"] > sub["goals_away"]])
    draws = len(sub[sub["goals_home"] == sub["goals_away"]])
    away_wins = len(sub[sub["goals_home"] < sub["goals_away"]])
    return {
        "home_win": home_wins / total_matches,
        "draw": draws / total_matches,
        "away_win": away_wins / total_matches
    }