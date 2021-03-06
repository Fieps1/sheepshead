from collections import namedtuple
from copy import deepcopy
from timeit import timeit
from typing import Tuple, List, Set

from card_types import *
from deck import count_score, create_shuffled_4_player_hands
from rules import Sauspiel, BasicTrumpGame, SauspielException

Tick = namedtuple('Tick', 'cards scoring_player')


class Turn(namedtuple('Turn', 'round player hand allowed_cards')):
    def __str__(self):
        return f'Round {self.round} player {self.player} with {self.hand} is allowed to play {self.allowed_cards}'


class Game:
    def __init__(self, mode, player_cards: List[Set[Card]], starting_player=0):
        self.mode: BasicTrumpGame = mode
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

    def get_scores_per_player(self) -> Tuple[int, ...]:
        scores = [0] * self.num_players
        for tick in self.past_ticks:
            scores[tick.scoring_player] += count_score(tick.cards)

        return tuple(scores)

    def get_scores_per_team(self) -> Tuple[int, ...]:
        # For 2 team games: 0 player team, 1 non-player team
        scores_per_player = self.get_scores_per_player()

        return tuple(map(lambda team: sum([scores_per_player[player] for player in team]), self.mode.teams))

    def _get_current_player_hand(self):
        return self.player_cards[self.current_player]

    def play_card(self, card):
        # Player must hold the card in hand
        if card not in self._get_current_player_hand():
            raise Exception("Attempted to play a card which isn't yours!")
        # Card must be allowed to play
        if card not in self.mode.allowed_cards(self.current_trick, self._get_current_player_hand()):
            raise Exception("You are not allowed to play this card!")

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

    def get_game_result(self):
        if self.is_finished():
            return self.mode.game_result(self.get_scores_per_team())
        else:
            raise Exception("Game is not over yet!")


def try_create_game():
    player_cards = create_shuffled_4_player_hands()

    try:
        sauspiel = Sauspiel(player_cards, rufsau=Card(EICHEL, SAU), playmaker=0)

        return Game(sauspiel, player_cards, starting_player=0)
    except SauspielException:
        print("recreating")
        return try_create_game()


def play_random_game():

    game = try_create_game()

    while not game.is_finished():
        turn = game.get_current_turn()
        # print(turn)
        card = turn.allowed_cards.pop()
        # print(f'Play {card}')
        game.play_card(card)
    print(game.get_game_result())
    if any(r > 20 for r in game.get_game_result()):
        print("error!")


if __name__ == '__main__':
    num_iterations = 500
    seconds = timeit(play_random_game, number=num_iterations)
    print(f'{num_iterations} games took {seconds} seconds')
    print(f'That is {num_iterations / seconds} iterations per second')


