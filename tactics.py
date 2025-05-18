# tactics.py

import pandas as pd
from gametheory import synergy_from_formation_style, calculate_combination_percentages

# === Formation Determination Functions ===

def is_442(team):
    return team.last_match_formation == '4-4-2'

def is_433(team):
    return team.last_match_formation == '4-3-3'

def is_352(team):
    return team.last_match_formation == '3-5-2'

def is_4231(team):
    return team.last_match_formation == '4-2-3-1'

def is_541(team):
    return team.last_match_formation == '5-4-1'

def is_343(team):
    return team.last_match_formation == '3-4-3'

def is_451(team):
    return team.last_match_formation == '4-5-1'

def is_3421(team):
    return team.last_match_formation == '3-4-2-1'

def is_4141(team):
    return team.last_match_formation == '4-1-4-1'

def is_4222(team):
    return team.last_match_formation == '4-2-2-2'

def is_5212(team):
    return team.last_match_formation == '5-2-1-2'

def is_532(team):
    return team.last_match_formation == '5-3-2'

def is_41212(team):
    return team.last_match_formation == '4-1-2-1-2'

def is_361(team):
    return team.last_match_formation == '3-6-1'

def is_433_variant(team):
    return team.last_match_formation == '4-3-3 (variant)'

def is_343_variant(team):
    return team.last_match_formation == '3-4-3 (variant)'

def is_4312(team):
    return team.last_match_formation == '4-3-1-2'

def is_4231_variant(team):
    return team.last_match_formation == '4-2-3-1 (variant)'

def is_442_diamond(team):
    return team.last_match_formation == '4-4-2 Diamond'

def is_361_variant(team):
    return team.last_match_formation == '3-6-1 (variant)'

# === Style Determination Functions (20 Styles) ===

def style_counter_attack(team):
    if team.possession_percentage and team.possession_percentage < 45:
        if team.shots_on_target and team.shots_on_target >= 5:
            return True
    return False

def style_possession_based(team):
    if team.possession_percentage and team.possession_percentage > 60:
        if team.shots_on_target and team.shots_on_target >= 10:
            if team.passing_accuracy and team.passing_accuracy > 85:
                return True
    return False

def style_high_press(team):
    if team.possession_percentage and team.possession_percentage > 50:
        if team.shots_on_target and team.shots_on_target >= 12:
            if team.passing_accuracy and team.passing_accuracy > 80:
                return True
    return False

def style_low_press(team):
    if team.possession_percentage and team.possession_percentage < 50:
        if team.shots_on_target and team.shots_on_target >= 8:
            if team.passing_accuracy and team.passing_accuracy < 75:
                return True
    return False

def style_fast_break(team):
    if team.possession_percentage and team.possession_percentage < 45:
        if team.shots_on_target and team.shots_on_target >= 9:
            return True
    return False

def style_ball_control(team):
    if team.possession_percentage and team.possession_percentage > 55:
        if team.shots_on_target and team.shots_on_target >= 10:
            if team.passing_accuracy and team.passing_accuracy > 83:
                return True
    return False

def style_flank_attack(team):
    if team.possession_percentage and team.possession_percentage > 55:
        if team.shots_on_target and team.shots_on_target >= 10:
            if team.total_shots and team.total_shots >= 15:
                return True
    return False

def style_midfield_control(team):
    if team.possession_percentage and team.possession_percentage > 60:
        if team.shots_on_target and team.shots_on_target >= 10:
            if team.passing_accuracy and team.passing_accuracy > 85:
                return True
    return False

def style_direct_play(team):
    if team.possession_percentage and team.possession_percentage < 50:
        if team.shots_on_target and team.shots_on_target >= 8:
            if team.passing_accuracy and team.passing_accuracy < 80:
                return True
    return False

def style_territorial(team):
    if team.possession_percentage and team.possession_percentage > 50:
        if team.shots_on_target and team.shots_on_target >= 9:
            if team.passing_accuracy and team.passing_accuracy > 80:
                return True
    return False

def style_park_the_bus(team):
    if team.possession_percentage and team.possession_percentage < 35:
        if team.shots_on_target and team.shots_on_target < 5:
            return True
    return False

def style_gengenpress(team):
    if team.possession_percentage and team.possession_percentage > 50:
        if team.shots_on_target and team.shots_on_target >= 12:
            if team.passing_accuracy and team.passing_accuracy > 75:
                if team.total_shots and team.total_shots >= 18:
                    return True
    return False

def style_long_ball(team):
    if team.possession_percentage and team.possession_percentage < 45:
        if team.shots_on_target and team.shots_on_target >= 7:
            if team.passing_accuracy and team.passing_accuracy < 78:
                return True
    return False

def style_tiki_taka(team):
    if team.possession_percentage and team.possession_percentage > 65:
        if team.passing_accuracy and team.passing_accuracy > 88:
            if team.shots_on_target and team.shots_on_target >= 10:
                return True
    return False

def style_defensive_solid(team):
    if team.possession_percentage and team.possession_percentage < 40:
        if team.shots_on_target and team.shots_on_target >= 6:
            if team.total_shots and team.total_shots < 12:
                return True
    return False

def style_wing_play(team):
    if team.possession_percentage and team.possession_percentage > 50:
        if team.shots_on_target and team.shots_on_target >= 8:
            if team.total_shots and team.total_shots >= 16:
                if team.passing_accuracy and team.passing_accuracy > 80:
                    return True
    return False

def style_overload_midfield(team):
    if team.possession_percentage and team.possession_percentage > 55:
        if team.shots_on_target and team.shots_on_target >= 11:
            if team.passing_accuracy and 40 < team.passing_accuracy < 90:
                if team.total_shots and team.total_shots >= 14:
                    return True
    return False

def style_slow_build_up(team):
    if team.possession_percentage and team.possession_percentage > 50:
        if team.shots_on_target and team.shots_on_target >= 8:
            if team.passing_accuracy and team.passing_accuracy > 82:
                if team.total_shots and team.total_shots < 15:
                    return True
    return False

def style_direct_counter(team):
    if team.possession_percentage and team.possession_percentage < 45:
        if team.shots_on_target and team.shots_on_target >= 10:
            if team.passing_accuracy and team.passing_accuracy < 80:
                return True
    return False

def style_clinical_finishing(team):
    if team.shots_on_target and team.shots_on_target >= 12:
        if team.total_shots and team.total_shots <= 16:
            if team.possession_percentage and 40 < team.possession_percentage < 60:
                return True
    return False

def determine_team_formation(team):
    """Belirler: Takımın son maç formasyonu."""
    checks = [
        ('4-4-2', is_442),
        ('4-3-3', is_433),
        ('3-5-2', is_352),
        ('4-2-3-1', is_4231),
        ('5-4-1', is_541),
        ('3-4-3', is_343),
        ('4-5-1', is_451),
        ('3-4-2-1', is_3421),
        ('4-1-4-1', is_4141),
        ('4-2-2-2', is_4222),
        ('5-2-1-2', is_5212),
        ('5-3-2', is_532),
        ('4-1-2-1-2', is_41212),
        ('3-6-1', is_361),
        ('4-3-3 (variant)', is_433_variant),
        ('3-4-3 (variant)', is_343_variant),
        ('4-3-1-2', is_4312),
        ('4-2-3-1 (variant)', is_4231_variant),
        ('4-4-2 Diamond', is_442_diamond),
        ('3-6-1 (variant)', is_361_variant)
    ]
    for formation_name, fn in checks:
        if fn(team):
            return formation_name
    return "Unknown Formation"

def determine_team_play_style(team):
    """Belirler: Takımın olası oyun tarzı."""
    checks = [
        ("Counter Attack", style_counter_attack),
        ("Possession Based", style_possession_based),
        ("High Press", style_high_press),
        ("Low Press", style_low_press),
        ("Fast Break", style_fast_break),
        ("Ball Control", style_ball_control),
        ("Flank Attack", style_flank_attack),
        ("Midfield Control", style_midfield_control),
        ("Direct Play", style_direct_play),
        ("Territorial", style_territorial),
        ("Park The Bus", style_park_the_bus),
        ("Gegenpress", style_gengenpress),
        ("Long Ball", style_long_ball),
        ("Tiki Taka", style_tiki_taka),
        ("Defensive Solid", style_defensive_solid),
        ("Wing Play", style_wing_play),
        ("Overload Midfield", style_overload_midfield),
        ("Slow Build Up", style_slow_build_up),
        ("Direct Counter", style_direct_counter),
        ("Clinical Finishing", style_clinical_finishing),
    ]
    for style_name, fn in checks:
        if fn(team):
            return style_name
    return "Balanced"  # Varsayılan tarz

# === New Game Theory Integration Functions ===

def get_game_theory_bonus(teamA, teamB, history_file="history_df.xlsx"):
    """
    Bu fonksiyon, verilen iki takımın (teamA ve teamB) son maç formasyonları ve oyun tarzlarını kullanarak,
    geçmiş verileri (history_df.xlsx) tarar ve gametheory.synergy_from_formation_style() kullanarak bonus hesaplar.
    
    teamA ve teamB nesneleri, en az şunlara sahip olmalıdır:
      - last_match_formation
      - style
      
    Döndürür: (bonusA, bonusB) ikilisi, yani her iki kombinasyon için ek güç katsayısı.
    """
    try:
        history_df = pd.read_excel(history_file)
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return (0.0, 0.0)
    
    formA = teamA.last_match_formation
    styleA = teamA.style
    formB = teamB.last_match_formation
    styleB = teamB.style
    bonusA, bonusB = synergy_from_formation_style(formA, styleA, formB, styleB, history_df)
    return bonusA, bonusB

def adjust_team_power_with_bonus(team, bonus):
    """
    Takımın base_strength değerine game theory bonus'unu ekleyerek, ayarlanmış güç değerini döndürür.
    team nesnesinin 'base_strength' attribute'nu içerdiğini varsayar.
    """
    if hasattr(team, 'base_strength'):
        return team.base_strength + bonus
    else:
        return bonus