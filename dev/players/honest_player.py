from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 1000

class HonestPlayer(BasePokerPlayer):
    
    def __init__(self):
        super().__init__()
        # Initialize tracking variables
        self.initial_stack = 0
        self.current_stack = 0
        self.total_gains_losses = 0
        self.round_gains_losses = {}  # Track gains/losses by round
        self.hand_stats = {
            'played': 0,
            'won': 0,
            'folded': 0
        }    

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )
        if win_rate >= 1.0 / self.nb_player:
            action = valid_actions[1]  # fetch CALL action info
            self.hand_stats['played'] += 1
        else:
            action = valid_actions[0]  # fetch FOLD action info
            self.hand_stats['folded'] += 1
            
        return action['action'], action['amount']

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']
        
                 # Initialize starting stack
        for player in game_info['seats']:
            if player['uuid'] == self.uuid:
                self.initial_stack = player['stack']
                self.current_stack = player['stack']
                break
            
        # print(f"Game started with stack: {self.initial_stack}")
        # Reset tracking for new game
        self.total_gains_losses = 0
        self.round_gains_losses = {}

    def receive_round_start_message(self, round_count, hole_card, seats):
          # Track the stack at the beginning of each round
        for seat in seats:
            if seat['uuid'] == self.uuid:
                stack_before_round = self.current_stack
                self.current_stack = seat['stack']
                
                # If it's not the first round, calculate gain/loss from previous round
                if round_count > 1:
                    previous_round = round_count - 1
                    round_result = self.current_stack - stack_before_round
                    self.round_gains_losses[previous_round] = round_result
                    self.total_gains_losses = self.current_stack - self.initial_stack
                    # print(f"Round {previous_round} completed - Gain/Loss: {round_result}, Total: {self.total_gains_losses}")
                break
        pass

    def receive_street_start_message(self, street, round_state):
                 # Update current stack at each street
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                self.current_stack = seat['stack']
                break
        pass

    def receive_game_update_message(self, action, round_state):
                # Update current stack when game state changes
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                self.current_stack = seat['stack']
                break
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
                 # Update stack after round ends
        round_count = round_state['round_count']
        
        # Check if I won this hand
        # i_won = False
        for winner in winners:
            if winner['uuid'] == self.uuid:
                # i_won = True
                self.hand_stats['won'] += 1
                break
        
        # Find my final stack for this round
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                new_stack = seat['stack']
                round_result = new_stack - self.current_stack
                self.current_stack = new_stack
                self.round_gains_losses[round_count] = round_result
                self.total_gains_losses = self.current_stack - self.initial_stack
                break
        pass
    
    def get_performance_stats(self):
        """Return comprehensive performance statistics"""
        win_rate = (self.hand_stats['won'] / self.hand_stats['played']) * 100 if self.hand_stats['played'] > 0 else 0
        fold_rate = (self.hand_stats['folded'] / self.hand_stats['played']) * 100 if self.hand_stats['played'] > 0 else 0
        
        return {
            'initial_stack': self.initial_stack,
            'current_stack': self.current_stack,
            'total_profit_loss': self.total_gains_losses,
            'profit_percentage': (self.total_gains_losses / self.initial_stack) * 100 if self.initial_stack > 0 else 0,
            'round_results': self.round_gains_losses,
            'hands_played': self.hand_stats['played'],
            'hands_won': self.hand_stats['won'],
            'hands_folded': self.hand_stats['folded'],
            'win_rate': win_rate,
            'fold_rate': fold_rate
        }

