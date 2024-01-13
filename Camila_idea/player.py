'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, BidAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import random
import eval7


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.activate_folds = False

        pass

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        pass

        card1 = my_cards[0]
        card2 = my_cards[1]

        rank1 = card1[0] # "Ad", "9c", "Th" -> "A", "9", "T"
        suit1 = card1[1] # "d", "c", "h", etc.
        rank2 = card2[0]
        suit2 = card2[1]

        game_clock = game_state.game_clock
        num_rounds = game_state.round_num

        forever_fold = (1.5 * (NUM_ROUNDS - round_num)) + 5

        if my_bankroll > forever_fold:
            self.activate_folds = True

        monte_carlo_iters = 200
        strength_w_auction, strength_wo_auction = self.calculate_strength(my_cards, monte_carlo_iters)
        self.strength_w_auction = strength_w_auction
        self.strength_wo_auction = strength_wo_auction

        print(self.activate_folds, "camila is annoying and wants to have text :(")

        if num_rounds == NUM_ROUNDS:
            print(game_clock)



    def calculate_strength(self, my_cards, iters):
        deck = eval7.Deck()
        my_cards = [eval7.Card(card) for card in my_cards]
        for card in my_cards:
            deck.cards.remove(card)
        wins_w_auction = 0
        wins_wo_auction = 0

        for i in range(iters):
            deck.shuffle()
            opp = 3
            community = 5
            draw = deck.peek(opp+community)
            opp_cards = draw[:opp]
            community_cards = draw[opp:]

            our_hand = my_cards + community_cards
            opp_hand = opp_cards + community_cards

            our_hand_val = eval7.evaluate(our_hand)
            opp_hand_val = eval7.evaluate(opp_hand)

            if our_hand_val > opp_hand_val:
                # We won the round
                wins_wo_auction += 2
            if our_hand_val == opp_hand_val:
                # We tied the round
                wins_wo_auction += 1
            else:
                # We lost the round
                wins_wo_auction

        for i in range(iters):
            deck.shuffle()
            opp = 2
            community = 5
            auction = 1
            draw = deck.peek(opp+community+auction)
            opp_cards = draw[:opp]
            community_cards = draw[opp: opp + community]
            auction_card = draw[opp+community:]
            our_hand = my_cards + auction_card + community_cards
            opp_hand = opp_cards + community_cards

            our_hand_val = eval7.evaluate(our_hand)
            opp_hand_val = eval7.evaluate(opp_hand)

            if our_hand_val > opp_hand_val:
                # We won the round
                wins_w_auction += 2
            elif our_hand_val == opp_hand_val:
                # we tied the round
                wins_w_auction += 1
            else:
                #We tied the round
                wins_w_auction += 0

            strength_w_auction = wins_w_auction / (2* iters)
            strength_wo_auction = wins_wo_auction/ (2* iters)

        return strength_w_auction, strength_wo_auction




    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        # May be useful, but you may choose to not use.
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        my_bid = round_state.bids[active]  # How much you bid previously (available only after auction)
        opp_bid = round_state.bids[1-active]  # How much opponent bid previously (available only after auction)
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        pot = my_contribution + opp_contribution

        if self.activate_folds == True:
            if CheckAction in legal_actions:
                return CheckAction()
            else:
                return FoldAction()

        def calculate_ShouldWeBidOnTheAuction(mycards, flopcards, iters):
            #this one will determine if we want to bid on auction
            #this is post flop so take that into account
            deck = eval7.Deck()
            mycards = [eval7.Card(card) for card in mycards]
            flopcards = [eval7.Card(card) for card in flopcards]
            for card in mycards:
                deck.cards.remove(card)
            for card in flopcards:
                deck.cards.remove(card) #deck without the flop cards and our cards
            wins_w_auction = 0
            wins_wo_auction = 0

            for i in range(iters): #without the auction
                deck.shuffle()
                opp = 3
                remaining_community_cards = 2
                draw = deck.peek(opp+remaining_community_cards)
                opp_cards = draw[:opp]
                new_community_cards = draw[opp:]
                community_cards = new_community_cards + flopcards

                our_hand = mycards + community_cards
                opp_hand = opp_cards + community_cards

                our_hand_val = eval7.evaluate(our_hand)
                opp_hand_val = eval7.evaluate(opp_hand)

                if our_hand_val > opp_hand_val:
                    # We won the round
                    wins_wo_auction += 1
                if our_hand_val == opp_hand_val:
                    # We tied the round
                    wins_wo_auction += .5
                else:
                    # We lost the round
                    wins_wo_auction

            for i in range(iters): #with the auction
                deck.shuffle()
                opp = 2
                remaining_community_cards = 2
                auction = 1
                draw = deck.peek(opp+remaining_community_cards+auction)
                opp_cards = draw[:opp]
                community_cards = draw[opp: opp + remaining_community_cards]
                community_cards = community_cards + flopcards
                auction_card = draw[opp+remaining_community_cards:]

                our_hand = mycards + auction_card + community_cards
                opp_hand = opp_cards + community_cards

                our_hand_val = eval7.evaluate(our_hand)
                opp_hand_val = eval7.evaluate(opp_hand)

                if our_hand_val > opp_hand_val:
                    # We won the round
                    wins_w_auction += 1
                elif our_hand_val == opp_hand_val:
                    # we tied the round
                    wins_w_auction += .5
                else:
                    #We tied the round
                    wins_w_auction += 0

            strength_w_auction = wins_w_auction / iters
            strength_wo_auction = wins_wo_auction / iters
                #return the decimal of the percentage of the number of times it won with the auction and without the auction
            return strength_w_auction- strength_wo_auction

        def calculate_TheOddsAfterTheAuction(cardswehave, thecardsontheboard, iters):
            #this one will calculate odds after the auction based on street
            wins = 0
            deck = eval7.Deck()
            reformattedcardsthatwehave = [eval7.Card(card) for card in cardswehave]
            reformattedboardcards = [eval7.Card(card) for card in thecardsontheboard]

            for card in reformattedcardsthatwehave:
                deck.cards.remove(card)
            for card in reformattedboardcards:
                deck.cards.remove(card)

            community = 5-len(reformattedboardcards)  #bring this outside the loop bc doesn't change
            opp = 5-len(reformattedcardsthatwehave)

            for i in range(iters):
                deck.shuffle()
                draw = deck.peek(opp+community)
                opp_cards = draw[:opp]
                if community == 0:
                    community_cards = reformattedboardcards
                else:
                    community_cards = draw[opp:]
                    community_cards = community_cards + reformattedboardcards

                our_hand = reformattedcardsthatwehave + community_cards
                opp_hand = opp_cards + community_cards

                our_hand_val = eval7.evaluate(our_hand)
                opp_hand_val = eval7.evaluate(opp_hand)

                if our_hand_val > opp_hand_val:
                    # We won the round
                    wins += 1
                if our_hand_val == opp_hand_val:
                    # We tied the round
                    wins += .5
                else:
                    # We lost the round
                    pass
            return wins/iters






        strength_diff = calculate_ShouldWeBidOnTheAuction(my_cards, board_cards, 200)

        if BidAction in legal_actions:
            max_bid_percentage = 1
            min_bid_percentage = 0
            bid_percentage = 1.5*strength_diff
            if bid_percentage > min_bid_percentage and bid_percentage < max_bid_percentage:
                bid = int(my_stack*bid_percentage)
                return BidAction(bid)
            elif bid_percentage<= min_bid_percentage:
                return BidAction(int(min_bid_percentage*pot))
            elif bid_percentage >= max_bid_percentage:
                return BidAction(int(max_bid_percentage*pot))

        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()


        if street < 3:
            strength = (self.strength_w_auction + self.strength_wo_auction)/2

            if strength > 0.6:
                if continue_cost > 50 or pot > 100:
                    return CallAction()
                elif random.random()>0.5:
                    raise_cost = continue_cost + 50
                else:
                    raise_cost = continue_cost + 100
            elif strength > 0.45:
                if continue_cost < 50:
                    if continue_cost > 10 or pot > 50:
                        return CallAction()
                    elif random.random()>0.5:
                        raise_cost = continue_cost + 25
                    elif CheckAction in legal_actions:
                        return CheckAction()
                    else:
                        return CallAction()
                else:
                    if CheckAction in legal_actions:
                        return CheckAction()
                    else:
                        return FoldAction()
            else:
                if CheckAction in legal_actions:
                    return CheckAction()
                else:
                    return FoldAction()

        else:
            strength = calculate_TheOddsAfterTheAuction(my_cards, board_cards, 200)

            raise_cost = int(continue_cost + 0.5*pot)

        if RaiseAction in legal_actions and raise_cost <= my_stack:
            raise_cost = max(min_raise,raise_cost)
            raise_cost = min(max_raise, raise_cost)
            commit_action = RaiseAction(int(raise_cost))
        elif CallAction in legal_actions and continue_cost <= my_stack:
            commit_action = CallAction()
        else:
            if CheckAction in legal_actions:
                commit_action = CheckAction()
            else:
                commit_action = FoldAction()

        if continue_cost > 0:
            pot_odds = continue_cost/(continue_cost + pot)

            if strength >= pot_odds:
                if strength > 0.95 and RaiseAction in legal_actions:
                    my_action = RaiseAction(max_raise)
                elif strength - pot_odds > 0.3:
                    my_action = commit_action
                elif strength - pot_odds > 0.2:
                    if random.random() > 0.5:
                        my_action = commit_action
                    else:
                        return CallAction()
                else:
                    return CallAction()


            if strength < pot_odds:
                if random.random() < 0.1:
                    if RaiseAction in legal_actions or CallAction in legal_actions:
                        my_action = commit_action
                else:
                    if CheckAction in legal_actions:
                        return CheckAction()
                    else:
                        return FoldAction()

        else:
            if strength > 0.95 and RaiseAction in legal_actions:
                my_action = RaiseAction(max_raise)
            elif strength > 0.8:
                my_action = commit_action
            elif strength > 0.65:
                if random.random() > 0.5:
                    my_action = commit_action
                else:
                    my_action = CheckAction()
            else:
                my_action = CheckAction()

        return my_action





if __name__ == '__main__':
    run_bot(Player(), parse_args())
