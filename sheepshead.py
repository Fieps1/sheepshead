from collections import namedtuple
from copy import deepcopy
from typing import Tuple

import numpy as np
from timeit import timeit
from deck import *


class BasicTrumpGame:

    def __init__(self, trump=HERZ, face_trump_order=(OBER, UNTER)):
        self.NON_TRUMP_ORDER = [face for face in Face if face not in face_trump_order]

        self.NON_TRUMP_FACE_RANKS = {face: power + 100 for power, face in enumerate(self.NON_TRUMP_ORDER)}

        self.TRUMP_ORDER = []
        for face_trump in face_trump_order:
            self.TRUMP_ORDER += [Card(s, face_trump) for s in Suit]
        self.TRUMP_ORDER += [Card(trump, f) for f in self.NON_TRUMP_ORDER]

        self.TRUMP_CARD_RANKS = {card: power for power, card in enumerate(self.TRUMP_ORDER)}

    def allowed_cards(self, layed_out_cards: List[Card], player_cards: Set[Card]) -> Set[Card]:
        if len(layed_out_cards) == 0:
            return player_cards

        first_card = layed_out_cards[0]

        if first_card in self.TRUMP_CARD_RANKS:
            matching_cards = {c for c in player_cards if c in self.TRUMP_CARD_RANKS}
        else:
            matching_cards = {c for c in player_cards if c.suit == first_card.suit
                              and c.face in self.NON_TRUMP_FACE_RANKS}

        if len(matching_cards) == 0:
            return deepcopy(player_cards)
        else:
            return matching_cards

    def winning_position(self, cards: List[Card]):
        first_suit = cards[0].suit

        def card_to_power(card):
            try:
                return self.TRUMP_CARD_RANKS[card]
            except KeyError:
                if card.suit == first_suit:
                    return self.NON_TRUMP_FACE_RANKS[card.face]
                else:
                    return 1000

        return np.argmin([card_to_power(card) for card in cards])


class Sauspiel:

    def __init__(self, player_cards: List[Set[Card]], rufsau: Card, playmaker: int, davon_laufen=False):
        self.rufsau = deepcopy(rufsau)
        self.davon_laufen = davon_laufen
        self.basic_game = BasicTrumpGame()
        self.teams = self._determine_teams(player_cards, playmaker)

    # chain this function after applying general_trump_game_rule
    def apply_rufsau_rule(self, layed_out_cards: List[Card], len_player_cards: int, allowed_cards: Set[Card]) -> Set[Card]:
        if self.rufsau in allowed_cards and len_player_cards != 1:
            if len(layed_out_cards) == 0:  # First card on the table
                call_suits = self.filter_rufsau_accompanying_cards(allowed_cards)
                if self.davon_laufen and len(call_suits) >= 3:
                    return deepcopy(allowed_cards)
                else:  # len(call_suits) < 3
                    return {card for card in allowed_cards if card not in call_suits}
            else:  # len(layed_out_cards) > 0
                if layed_out_cards[0].suit == self.rufsau.suit:
                    return {self.rufsau}
                else:  # Sau was not searched for, all cards except for Sau are allowed
                    return {card for card in allowed_cards if card != self.rufsau}
        else:
            return deepcopy(allowed_cards)

    def winning_position(self, *args):
        return self.basic_game.winning_position(*args)

    def allowed_cards(self, layed_out_cards: List[Card], player_cards: Set[Card]) -> Set[Card]:
        allowed_cards_base = self.basic_game.allowed_cards(layed_out_cards, player_cards)
        allowed_cards_sauspiel = self.apply_rufsau_rule(layed_out_cards, len(player_cards), allowed_cards_base)
        return allowed_cards_sauspiel

    def filter_rufsau_accompanying_cards(self, cards: Set[Card]) -> Set[Card]:
        return {card for card in cards if
                card.face in self.basic_game.NON_TRUMP_FACE_RANKS
                and card.suit == self.rufsau.suit
                and card != self.rufsau}

    def _determine_teams(self, player_cards, playmaker) -> Tuple[Set[int], Set[int]]:
        players = set()
        non_players = set()
        for it_player in range(len(player_cards)):
            if any([card == self.rufsau for card in player_cards[it_player]]):
                players.add(it_player)
            elif playmaker == it_player:
                players.add(it_player)
            else:
                non_players.add(it_player)

        return players, non_players


Tick = namedtuple('Tick', 'cards scoring_player')


class Turn(namedtuple('Turn', 'round player hand allowed_cards')):
    def __str__(self):
        return f'Round {self.round} player {self.player} with {self.hand} is allowed to play {self.allowed_cards}'


class Game:
    def __init__(self, mode, player_cards: List[Set[Card]], starting_player=0):
        self.mode: Sauspiel = mode
        self.player_cards: List[Set[Card]] = deepcopy(player_cards)
        self.num_players = len(player_cards)
        self.past_ticks: List[Tick] = []
        self.current_trick = []
        self.current_player = starting_player

    def resolve_tick_winner(self, current_player, winning_pos):
        winning_pos_relative_to_player = winning_pos - (self.num_players - 1)
        winning_player = current_player + winning_pos_relative_to_player  # can be negative
        return (winning_player + self.num_players) % self.num_players

    @property
    def teams(self):
        return self.mode.teams

    def is_finished(self):
        return not any(self.player_cards)

    def get_round(self):
        return len(self.past_ticks)

    def get_scores_per_player(self) -> Tuple[int]:
        scores = [0] * self.num_players
        for tick in self.past_ticks:
            scores[tick.scoring_player] += count_score(tick.cards)

        return tuple(scores)

    def get_scores_per_team(self) -> Tuple[int]:
        # 0 player team, 1 non-player team
        scores_per_player = self.get_scores_per_player()

        playmaker_scores = [scores_per_player[player] for player in self.mode.teams[0]]
        non_player_scores = [scores_per_player[player] for player in self.mode.teams[1]]

        return sum(playmaker_scores), sum(non_player_scores)

    def _get_current_player_hand(self):
        return self.player_cards[self.current_player]

    def play_card(self, card):
        # Player must hold the card in hand
        if card not in self._get_current_player_hand():
            raise Exception("Attempted to play a card which isn't yours!")
        # Card must be allowed to play
        if card not in self.mode.allowed_cards(self.current_trick, self._get_current_player_hand()):
            raise Exception("You are not allowed to play this card")

        # Execute move
        self._get_current_player_hand().remove(card)
        self.current_trick.append(card)

        # tick complete
        if len(self.current_trick) == self.num_players:
            # determine winner, give tick to him and set him as next player
            winning_pos = self.mode.winning_position(self.current_trick)
            winning_player = self.resolve_tick_winner(self.current_player, winning_pos)

            self.past_ticks.append(Tick(self.current_trick, winning_player))
            self.current_trick = []
            self.current_player = winning_player
        else:  # tick not complete
            self.current_player = (self.current_player + 1) % self.num_players

    def get_current_turn(self):
        return Turn(self.get_round(), self.current_player, self._get_current_player_hand(),
                    self.mode.allowed_cards(self.current_trick, self._get_current_player_hand()))


# todo: should be in the same module as sauspiel, but as free function?
def get_game_results(teams, scores_per_team) -> Tuple[int]:

    num_players = len(teams[0]) + len(teams[1])

    def create_result(score: int):
        return tuple(score if player in teams[0] else -score for player in range(num_players))

    if sum(scores_per_team) != 120:
        raise Exception('Total score at game end must be 120')

    player_score = scores_per_team[0]
    if player_score == 0:
        return create_result(-SCHNEIDER_SCHWARZ)
    if 0 < player_score <= 30:
        return create_result(-SCHNEIDER)
    if 30 < player_score <= 60:
        return create_result(-SPIEL)
    if 60 < player_score <= 90:
        return create_result(SPIEL)
    if 90 < player_score < 120:
        return create_result(SCHNEIDER)
    if player_score == 120:
        return create_result(SCHNEIDER_SCHWARZ)


SCHNEIDER_SCHWARZ = 30
SCHNEIDER = 20
SPIEL = 10


def play_random_game():
    player_cards = create_shuffled_player_hands()
    sauspiel = Sauspiel(player_cards, rufsau=Card(EICHEL, SAU), playmaker=0)
    game = Game(sauspiel, player_cards, starting_player=0)

    while not game.is_finished():
        turn = game.get_current_turn()
        # print(turn)
        card = turn.allowed_cards.pop()
        # print(f'Play {card}')
        game.play_card(card)


if __name__ == '__main__':
    num_iterations = 1000
    seconds = timeit(play_random_game, number=num_iterations)
    print(f'{num_iterations} games took {seconds} seconds')
    print(f'That is {num_iterations / seconds} iterations per second')
