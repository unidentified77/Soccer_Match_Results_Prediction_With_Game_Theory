# tactics.py

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

def style_counter_attack(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 40 and
            team.shots_on_target is not None and
            team.shots_on_target >= 8)

def style_possession_based(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 60 and
            team.shots_on_target is not None and team.shots_on_target >= 10 and
            team.passing_accuracy is not None and team.passing_accuracy > 85)

def style_high_press(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 50 and
            team.shots_on_target is not None and team.shots_on_target >= 12 and
            team.passing_accuracy is not None and team.passing_accuracy > 80)

def style_low_press(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 50 and
            team.shots_on_target is not None and team.shots_on_target >= 8 and
            team.passing_accuracy is not None and team.passing_accuracy < 75)

def style_fast_break(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 45 and
            team.shots_on_target is not None and team.shots_on_target >= 9)

def style_ball_control(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 55 and
            team.shots_on_target is not None and team.shots_on_target >= 10 and
            team.passing_accuracy is not None and team.passing_accuracy > 83)

def style_flank_attack(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 55 and
            team.shots_on_target is not None and team.shots_on_target >= 10 and
            team.total_shots is not None and team.total_shots >= 15)

def style_midfield_control(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 60 and
            team.shots_on_target is not None and team.shots_on_target >= 10 and
            team.passing_accuracy is not None and team.passing_accuracy > 85)

def style_direct_play(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 50 and
            team.shots_on_target is not None and team.shots_on_target >= 8 and
            team.passing_accuracy is not None and team.passing_accuracy < 80)

def style_territorial(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 50 and
            team.shots_on_target is not None and team.shots_on_target >= 9 and
            team.passing_accuracy is not None and team.passing_accuracy > 80)

def style_park_the_bus(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 35 and
            team.shots_on_target is not None and team.shots_on_target < 5)

def style_gengenpress(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 50 and
            team.shots_on_target is not None and team.shots_on_target >= 12 and
            team.passing_accuracy is not None and team.passing_accuracy > 75 and
            team.total_shots is not None and team.total_shots >= 18)

def style_long_ball(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 45 and
            team.shots_on_target is not None and team.shots_on_target >= 7 and
            team.passing_accuracy is not None and team.passing_accuracy < 78)

def style_tiki_taka(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 65 and
            team.passing_accuracy is not None and team.passing_accuracy > 88 and
            team.shots_on_target is not None and team.shots_on_target >= 10)

def style_defensive_solid(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 40 and
            team.shots_on_target is not None and team.shots_on_target >= 6 and
            team.total_shots is not None and team.total_shots < 12)

def style_wing_play(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 50 and
            team.shots_on_target is not None and team.shots_on_target >= 8 and
            team.total_shots is not None and team.total_shots >= 16 and
            team.passing_accuracy is not None and team.passing_accuracy > 80)

def style_overload_midfield(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 55 and
            team.shots_on_target is not None and team.shots_on_target >= 11 and
            team.passing_accuracy is not None and 40 < team.passing_accuracy < 90 and
            team.total_shots is not None and team.total_shots >= 14)

def style_slow_build_up(team):
    return (team.possession_percentage is not None and
            team.possession_percentage > 50 and
            team.shots_on_target is not None and team.shots_on_target >= 8 and
            team.passing_accuracy is not None and team.passing_accuracy > 82 and
            team.total_shots is not None and team.total_shots < 15)

def style_direct_counter(team):
    return (team.possession_percentage is not None and
            team.possession_percentage < 45 and
            team.shots_on_target is not None and team.shots_on_target >= 10 and
            team.passing_accuracy is not None and team.passing_accuracy < 80)

def style_clinical_finishing(team):
    return (team.shots_on_target is not None and team.shots_on_target >= 12 and
            team.total_shots is not None and team.total_shots <= 16 and
            team.possession_percentage is not None and 40 < team.possession_percentage < 60)

def determine_team_formation(team):
    formations = [
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
    for name, func in formations:
        if func(team):
            return name
    return 'Unknown Formation'

def determine_team_play_style(team):
    play_styles = [
        ('Counter Attack', style_counter_attack),
        ('Possession Based', style_possession_based),
        ('High Press', style_high_press),
        ('Low Press', style_low_press),
        ('Fast Break', style_fast_break),
        ('Ball Control', style_ball_control),
        ('Flank Attack', style_flank_attack),
        ('Midfield Control', style_midfield_control),
        ('Direct Play', style_direct_play),
        ('Territorial', style_territorial),
        ('Park The Bus', style_park_the_bus),
        ('Gegenpress', style_gengenpress),
        ('Long Ball', style_long_ball),
        ('Tiki Taka', style_tiki_taka),
        ('Defensive Solid', style_defensive_solid),
        ('Wing Play', style_wing_play),
        ('Overload Midfield', style_overload_midfield),
        ('Slow Build Up', style_slow_build_up),
        ('Direct Counter', style_direct_counter),
        ('Clinical Finishing', style_clinical_finishing)
    ]
    for name, func in play_styles:
        if func(team):
            return name
    return 'Unknown Play Style'
