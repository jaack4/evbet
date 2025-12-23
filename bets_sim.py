import random
import sys
from scipy.optimize import fsolve
from scipy.special import comb

prizepicks_power = {
    2 : 3,
    3 : 6,
    4 : 10,
    5 : 20,
    6 : 37.5,
}

prizepick_flex = {
    3 : {3:3, 2:1},
    4 : {4:6, 3:1.5},
    5 : {5:10, 4:2, 3:0.4},
    6 : {6:25, 5:2, 4:0.4},
}

class MonteCarloSimulator:
    def __init__():
        pass
    

def simulate_slip_probability(slip_type: str, num_legs: int, trials: int, win_prob: float=0.5) -> float:
    if slip_type == 'Power':
        pay = prizepicks_power
    else:
        pay = prizepick_flex
    
    payouts = []

    for trial in range(trials):
        legs_hit = 0
        for leg in range(num_legs):
            if random.random() < win_prob:
                legs_hit += 1
        payouts.append(pay[num_legs][legs_hit])
            


def calculate_breakeven(total_picks, payouts):
    """
    Calculates the break-even win probability (p) for a given slip structure.
    
    The Break-Even Point is defined as the win probability 'p' where:
    Expected Value (EV) = Wager amount (1 unit)
    
    Args:
        total_picks (int): Number of legs in the slip.
        payouts (dict or float): 
            - If float/int: It's a Power play (e.g., 10).
            - If dict: It's a Flex play mapping hits to payout (e.g., {5:10, 4:2}).
            
    Returns:
        float: The required win rate per leg (0.0 to 1.0).
    """
    
    # We define an equation where result = 0 means we have found the break-even point.
    # Equation: Expected_Return - Unit_Bet = 0
    def equation(p):
        expected_return = 0
        
        # --- Logic for Power Play (All-or-Nothing) ---
        if isinstance(payouts, (int, float)):
            # Probability of winning all legs = p ^ total_picks
            prob_win_all = p ** total_picks
            expected_return = prob_win_all * payouts
            
        # --- Logic for Flex Play (Binomial Distribution) ---
        else:
            # We must sum the EV of every possible winning outcome
            for hits, multiplier in payouts.items():
                # nCk formula: Number of ways to choose 'hits' winners out of 'total_picks'
                combinations = comb(total_picks, hits)
                
                # Probability of exactly 'hits' successes and rest failures
                # p^hits * (1-p)^(misses)
                prob_outcome = combinations * (p ** hits) * ((1 - p) ** (total_picks - hits))
                
                # Add to total expected return
                expected_return += prob_outcome * multiplier
        
        return expected_return - 1

    # Use fsolve to find the root of the equation (where EV - 1 = 0)
    # We provide an initial guess of 0.55 (55%) which is standard for props
    breakeven_p = fsolve(equation, 0.55)[0]
    
    return breakeven_p

def implied_odds(probability):
    """Converts a probability (0.0-1.0) to American Odds (e.g., -110)."""
    if probability == 0.5:
        return 100
    elif probability > 0.5:
        return - (probability / (1 - probability)) * 100
    else:
        return ((1 - probability) / probability) * 100

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    print(f"\n{'TYPE':<15} | {'PAYOUT STRUCTURE':<25} | {'BREAK-EVEN %':<12} | {'IMPLIED ODDS'}")
    print("=" * 70)

    # 1. Calculate Power Plays
    for picks, payout in prizepicks_power.items():
        be = calculate_breakeven(picks, payout)
        odds = implied_odds(be)
        
        payout_str = f"{payout}x"
        print(f"{picks}-Pick Power   | {payout_str:<25} | {be:.4%}     | {int(odds)}")

    print("-" * 70)

    # 2. Calculate Flex Plays
    for picks, payout_structure in prizepick_flex.items():
        be = calculate_breakeven(picks, payout_structure)
        odds = implied_odds(be)
        
        # Format the payout dict for cleaner reading
        # e.g., "5:10x, 4:2x"
        payout_str = ", ".join([f"{k}:{v}x" for k, v in payout_structure.items()])
        
        print(f"{picks}-Pick Flex    | {payout_str:<25} | {be:.4%}     | {int(odds)}")
