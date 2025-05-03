from pypokerengine.api.game import setup_config, start_poker
from players.fish_player import FishPlayer
from players.honest_player import HonestPlayer
from players.monte_player import MontePlayer
# from players.monte_player2 import MontePlayer2
from players.ai_player import AiPlayer
from players.cohere_player import CoherePlayer

monte = MontePlayer()
fish = FishPlayer()
honest = HonestPlayer()
cohere = CoherePlayer()
# gemini = AiPlayer()

config = setup_config(max_round=5, initial_stack=10000, small_blind_amount=5)
config.register_player(name="Fish", algorithm=fish)
config.register_player(name="Honest", algorithm=honest)
config.register_player(name="Monte", algorithm=monte)
config.register_player(name="Cohere", algorithm=cohere)
# config.register_player(name="Gemini", algorithm=gemini)

game_result = start_poker(config, verbose=1)


honest_stats = honest.get_performance_stats()
print("\nHonest Player Performance:")
print(f"Initial stack: {honest_stats['initial_stack']}")
print(f"Final stack: {honest_stats['current_stack']}")
print(f"Total profit/loss: {honest_stats['total_profit_loss']} ({honest_stats['profit_percentage']:.2f}%)")
print(f"Hands played: {honest_stats['hands_played']}")
print(f"Hands won: {honest_stats['hands_won']} (Win rate: {honest_stats['win_rate']:.2f}%)")
print(f"Hands folded: {honest_stats['hands_folded']} (Fold rate: {honest_stats['fold_rate']:.2f}%)")

monte_stats = monte.get_performance_stats()
print("\nMonte Player Performance:")
print(f"Initial stack: {monte_stats['initial_stack']}")
print(f"Final stack: {monte_stats['current_stack']}")
print(f"Total profit/loss: {monte_stats['total_profit_loss']} ({monte_stats['profit_percentage']:.2f}%)")
print(f"Hands played: {monte_stats['hands_played']}")
print(f"Hands won: {monte_stats['hands_won']} (Win rate: {monte_stats['win_rate']:.2f}%)")
# print(f"Rounds Won/Loss: {monte_stats['round_results']}")
print(f"Hands folded: {monte_stats['hands_folded']} (Fold rate: {monte_stats['fold_rate']:.2f}%)")

# monte2_stats = monte2.get_performance_stats()
# print("\nMonte2 Player Performance:")
# print(f"Initial stack: {monte2_stats['initial_stack']}")
# print(f"Final stack: {monte2_stats['current_stack']}")
# print(f"Total profit/loss: {monte2_stats['total_profit_loss']} ({monte2_stats['profit_percentage']:.2f}%)")
# print(f"Hands played: {monte2_stats['hands_played']}")
# print(f"Hands won: {monte2_stats['hands_won']} (Win rate: {monte2_stats['win_rate']:.2f}%)")
# print(f"Hands folded: {monte2_stats['hands_folded']} (Fold rate: {monte2_stats['fold_rate']:.2f}%)")

cohere_stats = cohere.get_performance_stats()
print("\nCohere Player Performance:")
print(f"Initial stack: {cohere_stats['initial_stack']}")
print(f"Final stack: {cohere_stats['current_stack']}")
print(f"Total profit/loss: {cohere_stats['total_profit_loss']} ({cohere_stats['profit_percentage']:.2f}%)")
print(f"Hands played: {cohere_stats['hands_played']}")
print(f"Hands won: {cohere_stats['hands_won']} (Win rate: {cohere_stats['win_rate']:.2f}%)")
print(f"Hands folded: {cohere_stats['hands_folded']} (Fold rate: {cohere_stats['fold_rate']:.2f}%)")