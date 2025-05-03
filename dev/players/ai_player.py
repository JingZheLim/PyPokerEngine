from pypokerengine.players import BasePokerPlayer
from openai import OpenAI
import json
API = ""
GEMAPI = ""


class AiPlayer(BasePokerPlayer):
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
            return raise_action['action'], bet
        elif action_decision["action"] == "CALL":
            return call['action'], call['amount']
        else:  # FOLD or any unrecognized action
            return fold['action'], fold['amount']

    def call_llm_api(self, game_state):
        # Format the prompt for the LLM
        prompt = f"""
            You are a professional poker player, playing against other professional poker players, you need to make the best move possible and you are trying to make the most amount of money over the long run. Evaluate the strength of the hand and consider the pot odds to make your decision.
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
            - "amount": an integer amount (only required if action is "RAISE")
            
            Example response:
            "action": "CALL"
            or
            "action": "RAISE", "amount": 50
            
            Provide a sentence after the json response of your reasoning why you made that decision
            """
        
        # Initialize OpenAI client with OpenRouter configuration
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=API,
        )
        
        # Make API call
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                    {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        llm_response = response.choices[0].message.content
        print("Raw LLM response:", llm_response)
        # file.write(llm_response)
        # file.write("\n") 
        # file.close()

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
        # Game info gives :
        # player_num (Number of players playing)
        # rules : {initial_stack': 100, 'max_round': 1, 'small_blind_amount': 5, 'ante': 0, 'blind_structure': {}}
        # seats (Players playing information) : {'name': 'Fish', 'uuid': 'ujjwyahvpvpeigcatpcxmh', 'stack': 100, 'state': 'participating'}

    def receive_round_start_message(self, round_count, hole_card, seats):
        # 1 round is the entire process of Flop, Turn, and River
        # round_count (counts the round it is current in)
        # hole_card (holds the hole card information of the player)
        # seats (Players playing information) (stack = money)
        pass

    def receive_street_start_message(self, street, round_state):
        # street is preflop, flop, turn, river

        # round_state gives : 
        # street : {'street' : 'preflop'}
        # pot : {'main': {'amount': 15}, 'side': []}
        # 'community_card': [], 'dealer_btn': 0, 'next_player': 0, 'small_blind_pos': 1, 'big_blind_pos': 2, 'round_count': 1, 'small_blind_amount': 5
        # seats (Players playing information) (stack = money)
        # action histories : {'preflop': [{'action': 'SMALLBLIND', 'amount': 5, 'add_amount': 5, 'uuid': 'aqkqtioikejuttreankpsh'}
        pass

    def receive_game_update_message(self, action, round_state):
        # action returns the actions of every player on the table
        # round_state gives : 
        # the street : {'street' : 'preflop'}
        # the pot : {'main': {'amount': 15}, 'side': []}
        # 'community_card': [], 'dealer_btn': 0, 'next_player': 0, 'small_blind_pos': 1, 'big_blind_pos': 2, 'round_count': 1, 'small_blind_amount': 5
        # seats (Players playing information) (stack = money)
        # action histories : {'preflop': [{'action': 'SMALLBLIND', 'amount': 5, 'add_amount': 5, 'uuid': 'aqkqtioikejuttreankpsh'}
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        # hand_info returns [] if ends before river
        # else hands of all players and their hand strength
        # {'uuid': 'wenfrdicjaiziwfodgbymz', 'hand': {'hand': {'strength': 'ONEPAIR', 'high': 13, 'low': 0}
        
        # winner returns the winner(s) information
        pass
