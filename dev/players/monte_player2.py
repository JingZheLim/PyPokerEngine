from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random

NB_SIMULATION = 1000

class MontePlayer2(BasePokerPlayer):
    
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
        fold = valid_actions[0]
        call = valid_actions[1]
        raise_action = valid_actions[2]
        
        community_card = round_state['community_card'] # Gets Communitiy Cards
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=NB_SIMULATION,
                nb_player=self.nb_player,
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )
        # Gets how much is in the pot    
        pot_size = round_state['pot']['main']['amount']
        
        # Get what the current round is whethere it is (preflop, flop, turn, river)
        street = round_state['street']
        
                
        # Calulating the pot odds
        # The ratio between the size of the pot and the amount needed to call
        current_highest_bet = 0
        my_current_bet = 0
        
        # Get the highest bet
        if street in round_state['action_histories']:
            for action_history in round_state['action_histories'][street]:
                if 'amount' in action_history:
                    current_highest_bet = max(current_highest_bet, action_history['amount'])
                
                # Get the highest bet that i've currently made
                if action_history['uuid'] == self.uuid and 'amount' in action_history:
                    my_current_bet = action_history['amount']
        
        # Calculate the call amount and the pot odds
        # The difference between the highest bet and what you've bet
        call_amount = current_highest_bet - my_current_bet
        
        pot_odds = call_amount / (pot_size + call_amount)
        
        
        min_raise = raise_action['amount']['min']
        max_raise = raise_action['amount']['max']
        print(f"Pot size: {pot_size}, Call amount: {call_amount}, Pot odds: {pot_odds}, Win Rate: {win_rate}")
        
         # Find my current stack from seats in round_state
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                self.current_stack = seat['stack']
                break
        
        if win_rate > 0.8:
            bet = max_raise  # Strong hands (raise big)
            self.hand_stats['played'] += 1
            return raise_action['action'], bet # call RAISE action with the max bet that you can
        
        elif win_rate > 0.6:
            bet = int(0.75 * pot_size)  # Strong but not dominating (raise 75% of pot)
            self.hand_stats['played'] += 1
            return raise_action['action'], bet # call RAISE action with to raise 75% of pot
        
        elif win_rate > 0.4:
            bet = min_raise  # Mediocre hands (raise small)
            self.hand_stats['played'] += 1
            return raise_action['action'], bet # call RAISE action with the minimum bet that you c
        
        
        elif win_rate < 0.3 and pot_odds < 0.2:  # Weak hand + bad pot odds
            action = fold # FOLD
            self.hand_stats['folded'] += 1
        else:
            action = call # CALL
            self.hand_stats['played'] += 1
            
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
        
        # Game info gives :
        # player_num (Number of players playing)
        # rules : {initial_stack': 100, 'max_round': 1, 'small_blind_amount': 5, 'ante': 0, 'blind_structure': {}}
        # seats (Players playing information) : {'name': 'Fish', 'uuid': 'ujjwyahvpvpeigcatpcxmh', 'stack': 100, 'state': 'participating'}

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
        # 1 round is the entire process of Flop, Turn, and River
        # round_count (counts the round it is current in)
        # hole_card (holds the hole card information of the player)
        # seats (Players playing information) (stack = money)
        pass

    def receive_street_start_message(self, street, round_state):
        
         # Update current stack at each street
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                self.current_stack = seat['stack']
                break
            
        
        # street is preflop, flop, turn, river

        # round_state gives : 
        # street : {'street' : 'preflop'}
        # pot : {'main': {'amount': 15}, 'side': []}
        # 'community_card': [], 'dealer_btn': 0, 'next_player': 0, 'small_blind_pos': 1, 'big_blind_pos': 2, 'round_count': 1, 'small_blind_amount': 5
        # seats (Players playing information) (stack = money)
        # action histories : {'preflop': [{'action': 'SMALLBLIND', 'amount': 5, 'add_amount': 5, 'uuid': 'aqkqtioikejuttreankpsh'}
        pass

    def receive_game_update_message(self, action, round_state):
        # Update current stack when game state changes
        for seat in round_state['seats']:
            if seat['uuid'] == self.uuid:
                self.current_stack = seat['stack']
                break
        
        # action returns the actions of every player on the table
        # round_state gives : 
        # the street : {'street' : 'preflop'}
        # the pot : {'main': {'amount': 15}, 'side': []}
        # 'community_card': [], 'dealer_btn': 0, 'next_player': 0, 'small_blind_pos': 1, 'big_blind_pos': 2, 'round_count': 1, 'small_blind_amount': 5
        # seats (Players playing information) (stack = money)
        # action histories : {'preflop': [{'action': 'SMALLBLIND', 'amount': 5, 'add_amount': 5, 'uuid': 'aqkqtioikejuttreankpsh'}
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
                
                # # Print detailed results
                # win_rate = (self.hand_stats['won'] / self.hand_stats['played']) * 100 if self.hand_stats['played'] > 0 else 0
                # print(f"Round {round_count} result: {'Won' if i_won else 'Lost'}")
                # print(f"Round {round_count} - Gain/Loss: {round_result}, Total: {self.total_gains_losses}")
                # print(f"Hands played: {self.hand_stats['played']}, Won: {self.hand_stats['won']}, Folded: {self.hand_stats['folded']}")
                # print(f"Win rate: {win_rate:.2f}%")
                break
        
        
        # hand_info returns [] if ends before river
        # else hands of all players and their hand strength
        # {'uuid': 'wenfrdicjaiziwfodgbymz', 'hand': {'hand': {'strength': 'ONEPAIR', 'high': 13, 'low': 0}
        
        # winner returns the winner(s) information
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

