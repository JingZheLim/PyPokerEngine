from pypokerengine.players import BasePokerPlayer
import cohere
import json

# Replace with your Cohere API key
COHERE_API_KEY = "lMWcC83xVJlxEE5RahrziIdTiVqGetOp7Ba9YtD4"


class CoherePlayer(BasePokerPlayer):
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
        
        community_card = round_state['community_card']
        pot_size = round_state['pot']['main']['amount']
        street = round_state['street']
        
        # Calculate current betting situation
        current_highest_bet = 0
        my_current_bet = 0
        
        if street in round_state['action_histories']:
            for action_history in round_state['action_histories'][street]:
                if 'amount' in action_history:
                    current_highest_bet = max(current_highest_bet, action_history['amount'])
                
                if action_history['uuid'] == self.uuid and 'amount' in action_history:
                    my_current_bet = action_history['amount']
        
        call_amount = current_highest_bet - my_current_bet
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0
        
        min_raise = raise_action['amount']['min']
        max_raise = raise_action['amount']['max']
        
        # Prepare game state for LLM API call
        game_state = {
            "hole_cards": hole_card,
            "community_cards": community_card,
            "pot_size": pot_size,
            "street": street,
            "call_amount": call_amount,
            "min_raise": min_raise,
            "max_raise": max_raise,
            "pot_odds": pot_odds
        }
        
        # Call LLM API to get decision
        action_decision = self.call_llm_api(game_state)
        
        # Process the LLM response
        if action_decision["action"] == "RAISE":
            bet = min(max(action_decision["amount"], min_raise), max_raise)
            self.hand_stats['played'] += 1
            return raise_action['action'], bet
        elif action_decision["action"] == "CALL":
            self.hand_stats['played'] += 1
            return call['action'], call['amount']
        else:  # FOLD or any unrecognized action
            self.hand_stats['folded'] += 1
            return fold['action'], fold['amount']

    def call_llm_api(self, game_state):
        # Prompt to send to Cohere
        prompt = f"""
            You are a professional poker player, playing against other professional poker players and they can call bluffs easily, you need to make the best possible move to make the most amount of money over the long run. Evaluate the strength of the hand and consider the pot odds to make your decision.
            Here is the current game state:
            - Your hole cards: {game_state['hole_cards']}
            - Community cards: {game_state['community_cards']}
            - Current street: {game_state['street']}
            - Pot size: {game_state['pot_size']}
            - Call amount: {game_state['call_amount']}
            - Minimum raise: {game_state['min_raise']}
            - Maximum raise: {game_state['max_raise']}
            - Pot odds: {game_state['pot_odds']:.2f}
                        
            Format your response strictly as a JSON object with:
            - "action": either "FOLD", "CALL", or "RAISE"
            - "amount": an integer amount in range of Minimum and Maximum raise (only required if action is "RAISE")
            
            Example response:
            "action": "CALL"
            or
            "action": "RAISE", "amount": 50
            
            Provide a sentence after the json response of your reasoning why you made that decision
            """
            
        file = open("history.txt", "a")
        # print(prompt)
        # file.write(prompt) 
        # file.write("\n") 
        # Initialize Cohere client
        client = cohere.Client(COHERE_API_KEY)        
            
        # Make API call
        response = client.generate(
                model="command",  # Use the appropriate model for your needs
                prompt=prompt,
                max_tokens=300,
                temperature=0.6,
                k=0
            )
        
        llm_response = response.generations[0].text.strip()
        print("Raw LLM response:", llm_response)
        file.write(llm_response)
        file.write("\n") 
        file.close()
        
        # Try to parse the response as JSON
        try:
            # Find JSON content in the response (in case there's extra text)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                action_dict = json.loads(json_str)
                
                # Validate the action dictionary
                if "action" not in action_dict:
                    print("Action not found in response, defaulting to FOLD")
                    return {"action": "FOLD"}
                
                # Ensure action is valid
                action = action_dict["action"].upper()
                if action not in ["FOLD", "CALL", "RAISE"]:
                    print(f"Invalid action '{action}', defaulting to FOLD")
                    return {"action": "FOLD"}
                
                # Ensure amount is present for RAISE
                if action == "RAISE" and "amount" not in action_dict:
                    print("Amount not specified for RAISE, using minimum raise")
                    action_dict["amount"] = game_state["min_raise"]
                
                return {"action": action, "amount": action_dict.get("amount", 0)}
            else:
                print("JSON structure not found in response, defaulting to FOLD")
                return {"action": "FOLD"}
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print("Defaulting to FOLD")
            return {"action": "FOLD"}
        except Exception as e:
            print(f"Unexpected error while processing LLM response: {e}")
            print("Defaulting to FOLD")
            return {"action": "FOLD"}     
              

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