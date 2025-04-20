from pypokerengine.api.game import setup_config, start_poker
from players.fish_player import FishPlayer
from players.honest_player import HonestPlayer
from players.monte_player import MontePlayer


config = setup_config(max_round=100, initial_stack=10000, small_blind_amount=5)
config.register_player(name="Fish", algorithm=FishPlayer())
config.register_player(name="Honest", algorithm=HonestPlayer())
config.register_player(name="Monte", algorithm=MontePlayer())
game_result = start_poker(config, verbose=1)