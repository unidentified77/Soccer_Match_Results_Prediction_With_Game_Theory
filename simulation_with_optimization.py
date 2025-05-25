import pandas as pd
import random
from scipy.optimize import differential_evolution

# Load your match data
df = pd.read_excel("updated_predictions.xlsx")

# Define strategy keys
STRATEGY_KEYS = [
    ('attack', 'attack'),
    ('attack', 'balance'),
    ('attack', 'defense'),
    ('balance', 'attack'),
    ('balance', 'balance'),
    ('balance', 'defense'),
    ('defense', 'attack'),
    ('defense', 'balance'),
    ('defense', 'defense'),
]

# Define style probabilities (unchanged)
STYLE_PROBABILITIES = {
    "Counter Attack": (0.45, 0.30, 0.25),
    "Possession Based": (0.30, 0.50, 0.20),
    "High Press": (0.50, 0.30, 0.20),
    "Low Press": (0.20, 0.30, 0.50),
    "Fast Break": (0.50, 0.25, 0.25),
    "Ball Control": (0.30, 0.50, 0.20),
    "Flank Attack": (0.45, 0.35, 0.20),
    "Midfield Control": (0.30, 0.50, 0.20),
    "Direct Play": (0.40, 0.35, 0.25),
    "Territorial": (0.35, 0.45, 0.20),
    "Park The Bus": (0.15, 0.25, 0.60),
    "Gegenpress": (0.50, 0.30, 0.20),
    "Long Ball": (0.40, 0.30, 0.30),
    "Tiki Taka": (0.35, 0.50, 0.15),
    "Defensive Solid": (0.20, 0.35, 0.45),
    "Wing Play": (0.45, 0.35, 0.20),
    "Overload Midfield": (0.30, 0.50, 0.20),
    "Slow Build Up": (0.25, 0.55, 0.20),
    "Direct Counter": (0.50, 0.25, 0.25),
    "Clinical Finishing": (0.50, 0.30, 0.20),
    "Balanced": (0.33, 0.33, 0.33)
}

def adjust_probabilities(base_probs, power_diff):
    attack, balance, defense = base_probs
    adj = min(0.1, abs(power_diff) / 15 * 0.1)
    if power_diff > 0:
        attack += adj
        defense -= adj
    else:
        attack -= adj
        defense += adj
    balance = 1 - attack - defense
    return {'attack': attack, 'balance': balance, 'defense': defense}

def simulate_match(home_style, away_style, home_power, away_power, payoff_matrix):
    power_diff = home_power - away_power
    home_probs = adjust_probabilities(STYLE_PROBABILITIES.get(home_style, (0.33, 0.33, 0.33)), power_diff)
    away_probs = adjust_probabilities(STYLE_PROBABILITIES.get(away_style, (0.33, 0.33, 0.33)), -power_diff)
    
    home_goals, away_goals = 0, 0
    for _ in range(90):
        h_choice = random.choices(list(home_probs.keys()), weights=home_probs.values())[0]
        a_choice = random.choices(list(away_probs.keys()), weights=away_probs.values())[0]
        h_prob, a_prob = payoff_matrix[(h_choice, a_choice)]
        if random.random() < h_prob:
            home_goals += 1
        if random.random() < a_prob:
            away_goals += 1
    return home_goals, away_goals

def simulate_10_matches(home_style, away_style, home_power, away_power, payoff_matrix):
    random.seed(42)
    h_total, a_total = 0, 0
    for _ in range(10):
        h, a = simulate_match(home_style, away_style, home_power, away_power, payoff_matrix)
        h_total += h
        a_total += a
    return h_total / 10, a_total / 10

# Extract real scores
def parse_score(score_str):
    try:
        h, a = score_str.split('-')
        return float(h), float(a)
    except:
        return None, None

# Loss function to minimize
def loss_function(flat_payoffs):
    # Convert flat list back to payoff matrix
    payoff_matrix = {k: (flat_payoffs[i], flat_payoffs[i + 1]) for i, k in zip(range(0, len(flat_payoffs), 2), STRATEGY_KEYS)}
    
    total_error = 0.0
    for _, row in df.iterrows():
        home_style = "Balanced"  # Or load from row if available
        away_style = "Balanced"
        home_power = row['Home_Power']
        away_power = row['Away_Power']
        pred_h, pred_a = simulate_10_matches(home_style, away_style, home_power, away_power, payoff_matrix)
        real_h, real_a = parse_score(row['Match_Score'])
        if real_h is not None:
            total_error += (real_h - pred_h) ** 2 + (real_a - pred_a) ** 2
    
    return total_error

# Initial bounds: each probability ∈ [0.0, 0.2]
bounds = [(0.0, 0.2)] * (len(STRATEGY_KEYS) * 2)

# Run optimizer
result = differential_evolution(loss_function, bounds, maxiter=50, disp=True)

# Reconstruct optimized matrix
optimized_matrix = {k: (result.x[i], result.x[i + 1]) for i, k in zip(range(0, len(result.x), 2), STRATEGY_KEYS)}

# Display optimized matrix
print("\n✅ Optimized PAYOFF_MATRIX:")
for k, v in optimized_matrix.items():
    print(f"{k}: Home Chance = {v[0]:.4f}, Away Chance = {v[1]:.4f}")
