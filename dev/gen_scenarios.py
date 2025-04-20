from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random
import json
import datetime

def generate_test_scenarios(num_scenarios=100):
    """
    Generate test scenarios with pre-calculated winning probabilities
    This would normally be a separate process preparing scenarios ahead of time
    """
    scenarios = []
    
    # For demonstration, we'll create simple scenarios
    # In a real implementation, you would have more diverse and realistic scenarios
    
    suits = ["H", "S", "D", "C"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]
    
    for i in range(num_scenarios):
        # Generate random hole cards
        hole_cards = []
        used_cards = set()
        
        for j in range(2):
            while True:
                suit = random.choice(suits)
                rank = random.choice(ranks)
                card = suit + rank
                if card not in used_cards:
                    hole_cards.append(card)
                    used_cards.add(card)
                    break
        
        # Generate random community cards (0-5 cards)
        num_community = random.randint(0, 5)
        community_cards = []
        
        for j in range(num_community):
            while True:
                suit = random.choice(suits)
                rank = random.choice(ranks)
                card = suit + rank
                if card not in used_cards:
                    community_cards.append(card)
                    used_cards.add(card)
                    break
        
        # Calculate true winning probability (run many simulations)
        true_probability = estimate_hand_win_probability(hole_cards, community_cards, num_opponents=1)
        
        scenarios.append({
            "hole_cards": hole_cards,
            "community_cards": community_cards,
            "true_win_probability": true_probability
        })
    
    return scenarios


def estimate_hand_win_probability(hole_cards, community_cards, num_opponents=1, num_simulations=10000):
    """
    Estimate the winning probability of a hand using Monte Carlo simulation
    """
    # Convert string representations to Card objects
    hole_card_objects = gen_cards(hole_cards)
    community_card_objects = gen_cards(community_cards)
    
    # Use pypokerengine's built-in win rate estimator
    win_rate = estimate_hole_card_win_rate(
        nb_simulation=num_simulations,
        nb_player=num_opponents + 1,  # Include our player
        hole_card=hole_card_objects,
        community_card=community_card_objects
    )
    
    return win_rate


def save_scenarios_to_json(scenarios, filename="poker_test_scenarios.json"):
    """
    Save generated test scenarios to a JSON file
    
    Args:
        scenarios: List of scenario dictionaries
        filename: Name of the output file
    """
    with open(filename, 'w') as f:
        json.dump({
            "metadata": {
                "num_scenarios": len(scenarios),
                "created_date": str(datetime.datetime.now()),
                "description": "Poker hand win probability test scenarios"
            },
            "scenarios": scenarios
        }, f, indent=2)
    
    print(f"Successfully saved {len(scenarios)} test scenarios to {filename}")
    
    
if __name__ == "__main__":
    # Generate scenarios
    print("Generating test scenarios...")
    scenarios = generate_test_scenarios(num_scenarios=50)
    
    # Save to file
    save_scenarios_to_json(scenarios)