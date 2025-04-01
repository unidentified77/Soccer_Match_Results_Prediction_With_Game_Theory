# gametheory.py

from utils import pd, np

def synergy_from_formation_style(formA, styA, formB, styB, history_df):
    """
    Given a desired matchup combination (formation and style for both sides)
    and a history DataFrame (with columns:
      - Formation_home, style_home, Formation_away, style_away,
      - goals_home, goals_away, etc.),
    filter the data for the last 10 matches that match the combination in either orientation,
    and compute bonus synergies:
      - If the team with (formA, styA) was home and won, add bonus.
      - Similarly for the away side.
    Returns a tuple (bonusA, bonusB)
    """
    sub = history_df.loc[
        ((history_df["Formation_home"] == formA) &
         (history_df["style_home"] == styA) &
         (history_df["Formation_away"] == formB) &
         (history_df["style_away"] == styB))
        |
        ((history_df["Formation_home"] == formB) &
         (history_df["style_home"] == styB) &
         (history_df["Formation_away"] == formA) &
         (history_df["style_away"] == styA))
    ]
    # Look at the last 10 matches
    sub = sub.tail(10)
    if sub.empty:
        return (0.0, 0.0)
    a_bonus = 0.0
    b_bonus = 0.0
    for _, row in sub.iterrows():
        hg = row["goals_home"]
        ag = row["goals_away"]
        if hg > ag:
            # Home win: if the home side used (formA, styA) then add bonus; otherwise add to opponent
            if row["Formation_home"] == formA and row["style_home"] == styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3
        elif ag > hg:
            # Away win: if the away side used (formA, styA) then add bonus
            if row["Formation_away"] == formA and row["style_away"] == styA:
                a_bonus += 0.3
            else:
                b_bonus += 0.3
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