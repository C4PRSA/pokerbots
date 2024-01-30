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
import pickle
import time



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

        self.opp_holes = []
        self.opp_bids = []
        self.min_opp_bid = 0
        self.max_opp_bid = 0

        prev_time = time.time()
        with open("hand_strengths", "rb") as file:
            self.starting_strengths = pickle.load(file)

        rank_to_numeric = dict()

        for i in range(2,10):
            rank_to_numeric[str(i)] = i

        for num, rank in enumerate("TJQKA"): #[(0,T), (1,J), (2,Q) ...]
            rank_to_numeric[rank] = num + 10

        self.rank_to_numeric = rank_to_numeric

        self.num_showdowns = 0
        self.opp_avg_strength = 0.5

        self.Last_20_Opp_Cards = []
        self.list_of_all_board_cards = []
        self.list_of_opp_strength_at_showdown = []
        self.opp_showdown_strength = .5


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

        game_clock = game_state.game_clock
        num_rounds = game_state.round_num


        # forever_fold = (1.5 * (NUM_ROUNDS - round_num)) + 2 #we always fold if were up by enough
        # if my_bankroll > forever_fold:
        #     self.activate_folds = True

        print("--------Round", round_num, "-------------")

        self.early_game = (round_num < 1000)

        card_strength = self.hand_to_strength(my_cards)
        self.card_strength = (card_strength[0] + card_strength[1])/2

        if self.activate_folds == True:
            print("we are always folding.")

        if num_rounds == NUM_ROUNDS:
            print(game_clock)


    def hand_to_strength(self, my_cards): #AcKs, Jc9s
        card_1 = my_cards[0]
        card_2 = my_cards[1]

        rank_1, suit_1 = card_1
        rank_2, suit_2 = card_2

        num_1 = self.rank_to_numeric[rank_1]
        num_2 = self.rank_to_numeric[rank_2]

        suited = 'o'
        if suit_1 == suit_2:
            suited = "s"

        if num_1 >= num_2:
            key = rank_1 + rank_2 + suited
        else:
            key = rank_2 + rank_1 + suited

        return self.starting_strengths[key]




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
        opp_bid = previous_state.bids[1-active]

        print("our delta:", my_delta)

        if len(opp_cards) >= 2 and self.activate_folds == False:

            if (self.num_showdowns) >= 20:     #if more than 20 showdowns have occured
                self.Last_20_Opp_Cards.pop(0)    #update to only include the last 20
                self.Last_20_Opp_Cards.append(opp_cards)
            else:
                self.Last_20_Opp_Cards.append(opp_cards) #if less than 20 occur we add to the list

            opp_cur_strength = self.hand_to_strength(opp_cards[:2])
            opp_cur_strength = (opp_cur_strength[0] + opp_cur_strength[1])/2

            if (self.num_showdowns) < 20:   #if less than 20 occur we calculate average opp strength
                self.opp_avg_strength = (self.opp_avg_strength *self.num_showdowns + opp_cur_strength) /(self.num_showdowns + 1)
            else:
                self.opp_avg_strength = .5   #if more than 20 showdowns have occured we calcuate average strength using the last 20
                for i in range(len(self.Last_20_Opp_Cards)):
                    opp_cur_strength = self.hand_to_strength(self.Last_20_Opp_Cards[i][:2])
                    opp_cur_strength = (opp_cur_strength[0] + opp_cur_strength[1])/2
                    self.opp_avg_strength = (self.opp_avg_strength * i + opp_cur_strength) / (i+1)

            self.num_showdowns += 1
            self.opp_bids.append(opp_bid)
            self.max_opp_bid = max(self.opp_bids)
            self.min_opp_bid = max(min(self.opp_bids), 51)



            lastboardcards = self.list_of_all_board_cards[-1] + opp_cards
            ReformattedBoardCards = [eval7.Card(card) for card in lastboardcards]   #eval7's to get the strenth of opp hand with relation to board cards at that time.
            opp_hand_val = eval7.evaluate(ReformattedBoardCards)

            if len(self.list_of_opp_strength_at_showdown) >= 20:   #makes an average of the last 20 strengths
                self.list_of_opp_strength_at_showdown.pop(0)
                self.list_of_opp_strength_at_showdown.append(opp_hand_val)
                self.opp_showdown_strength = sum(self.list_of_opp_strength_at_showdown) / 20
            else:
                self.list_of_opp_strength_at_showdown.append(opp_hand_val)
                self.opp_showdown_strength = sum(self.list_of_opp_strength_at_showdown) / len(self.list_of_opp_strength_at_showdown)

            self.list_of_all_board_cards.clear()

        elif self.activate_folds == False:
            self.list_of_all_board_cards.clear()








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

        if self.activate_folds == False:
            self.list_of_all_board_cards.append(board_cards)



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

            return strength_w_auction - strength_wo_auction

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

            if street == 5 and len(self.list_of_opp_strength_at_showdown) >= 10:    #uses the opp strength at showdown to calculate odds of winning

                for i in self.list_of_opp_strength_at_showdown:
                    #print("average opp showdown strength used in monte carlo:", i)
                    deck.shuffle()
                    draw = deck.peek(community)
                    if community == 0:
                        community_cards = reformattedboardcards
                    else:
                        community_cards = draw
                        community_cards = community_cards + reformattedboardcards

                    our_hand = reformattedcardsthatwehave + community_cards
                    our_hand_val = eval7.evaluate(our_hand)
                    #print("our hand value used in monte carlo:", our_hand_val)

                    if our_hand_val > i:
                        # We won the round
                        wins += 1
                    if our_hand_val == i:
                        # We tied the round
                        wins += .5
                    else:
                        # We lost the round
                        pass
                return wins/len(self.list_of_opp_strength_at_showdown)

            else:      #uses random opp cards for the flop
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

#########################################################################################################################
#########################################################################################################################
#########################################################################################################################

        #calculating our strength with monte carlo, to be used later
        if street == 3:
            strength = calculate_TheOddsAfterTheAuction(my_cards, board_cards, 150)
            print("Flop Strength:", strength)
        elif street == 4:
            strength = calculate_TheOddsAfterTheAuction(my_cards, board_cards, 150)
            print("Turn Strength:", strength)
        elif street == 5:
            strength = calculate_TheOddsAfterTheAuction(my_cards, board_cards, 150)
            print("River Strength:", strength)

        ##bidding on the auction
        if BidAction in legal_actions:
            strength_diff = calculate_ShouldWeBidOnTheAuction(my_cards, board_cards, 150)
            print("our strength difference is :", strength_diff)
            if self.early_game == True:
                max_bid_percentage = 1
                min_bid_percentage = 0
                bid_percentage = strength_diff
                if my_stack < 10:    #if we have less than 10 we bid our entire stack
                    return BidAction(my_stack)
                if bid_percentage > min_bid_percentage: #if were more liekly to win than lose
                    bid = int(my_stack*bid_percentage) #bid our stack *precentage we win
                    return BidAction(bid)
                elif bid_percentage<= min_bid_percentage:
                    return BidAction(int(min_bid_percentage*pot))
                elif bid_percentage >= max_bid_percentage:
                    return BidAction(int(max_bid_percentage*pot))
            else:
                if my_stack < 50:
                    return BidAction(my_stack)
                if strength_diff > 0.35:
                    return BidAction(min(my_stack, self.max_opp_bid+1))
                else:
                    return BidAction(min(my_stack, self.min_opp_bid-1))


        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()


       #########################################################

       ##########     Pre flop          ########################

       #########################################################
        if street < 3:
            strength = self.card_strength
            print("Preflop strength:", strength)
        ########Early game (not taking opp strength into account)#####
        if street < 3 and self.early_game == True:
            if strength > 0.6:
                if continue_cost > 50 or pot > 100:
                    return CallAction()
                elif random.random()>0.5:
                    raise_cost = continue_cost + 50
                else:
                    raise_cost = continue_cost + 100
            elif strength > 0.47:
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
            return RaiseAction(raise_cost)

        ########Late game (taking opp strength into account)#############

        elif street < 3 and self.early_game == False:
            print("Preflop strenght(opp):", self.opp_avg_strength)
            if strength > self.opp_avg_strength + 0.1:
                if continue_cost > 50 or pot > 100:
                    return CallAction()
                elif random.random()>0.5:
                    raise_cost = continue_cost + 50
                else:
                    raise_cost = continue_cost + 100
            elif strength > self.opp_avg_strength - 0.05:
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
            return RaiseAction(raise_cost)

    #########################################################

    ##########     Post flop          ########################

    #########################################################

        #########pot size too small for pot odds########

        elif pot<50:
            #######early game (no opp strength)###########
            if self.early_game == True:
                if strength > 0.7:
                    if continue_cost > 50 or pot > 100:
                        return CallAction()
                    elif random.random()>0.5:
                        raise_cost = continue_cost + 50
                    else:
                        raise_cost = continue_cost + 100
                elif strength > 0.5:
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
                elif strength > 0.37:
                    if CheckAction in legal_actions:
                        return CheckAction()
                    elif continue_cost < 10:
                        return CallAction()
                    else:
                        return FoldAction()
                else:
                    if CheckAction in legal_actions:
                        return CheckAction()
                    else:
                        return FoldAction()
                return RaiseAction(raise_cost)

            #####Late game (using opp pre flop strength)###############
            elif self.early_game == False:
                if strength > self.opp_avg_strength + 0.25:
                    if continue_cost > 50 or pot > 100:
                        return CallAction()
                    elif random.random()>0.5:
                        raise_cost = continue_cost + 50
                    else:
                        raise_cost = continue_cost + 100
                elif strength > self.opp_avg_strength:
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
            return RaiseAction(raise_cost)


        ########  large enough pot to use pot odds #################
        else:
            raise_cost_strong = int(continue_cost + 0.5*pot)
            raise_cost_weak = int(continue_cost + 0.25*pot)

        if RaiseAction in legal_actions and raise_cost_strong <= my_stack:
            raise_cost_strong = max(min_raise,raise_cost_strong)
            raise_cost_strong = min(max_raise, raise_cost_strong)
            commit_action_strong = RaiseAction(int(raise_cost_strong))
        elif CallAction in legal_actions and continue_cost <= my_stack:
            commit_action_strong = CallAction()
        else:
            if CheckAction in legal_actions:
                commit_action_strong = CheckAction()
            else:
                commit_action_strong = FoldAction()

        if RaiseAction in legal_actions and raise_cost_weak <= my_stack:
            raise_cost_weak = max(min_raise,raise_cost_weak)
            raise_cost_weak = min(max_raise, raise_cost_weak)
            commit_action_weak = RaiseAction(int(raise_cost_weak))
        elif CallAction in legal_actions and continue_cost <= my_stack:
            commit_action_weak = CallAction()
        else:
            if CheckAction in legal_actions:
                commit_action_weak = CheckAction()
            else:
                commit_action_weak = FoldAction()

        if continue_cost > 0:
            pot_odds = continue_cost/(continue_cost + pot)
            print("pot odds:", pot_odds)
            if strength >= pot_odds:
                if strength > 0.95 and RaiseAction in legal_actions:
                    my_action = RaiseAction(max_raise)
                elif strength - pot_odds > 0.4:
                    my_action = commit_action_strong
                elif strength - pot_odds > 0.27:
                    if random.random() > 0.5:
                        my_action = commit_action_weak
                    else:
                        return CallAction()
                else:
                    return CallAction()

            #######bluff when we should normally fold########
            elif strength < pot_odds:
                if random.random() < 0.05 and RaiseAction in legal_actions and raise_cost_strong/max_raise <0.5:
                    my_action = commit_action_strong
                else:
                    if CheckAction in legal_actions:
                        return CheckAction()
                    else:
                        return FoldAction()

        #### our job to either check or bet###########
        else:
            if strength > 0.95 and RaiseAction in legal_actions:
                my_action = RaiseAction(max_raise)
            elif strength > 0.8:
                my_action = commit_action_strong
            elif strength > 0.6:
                if random.random() > 0.5:
                    my_action = commit_action_weak
                else:
                    my_action = CheckAction()
            else:
                my_action = CheckAction()

        return my_action





if __name__ == '__main__':
    run_bot(Player(), parse_args())
