import random
from random import shuffle
from typing import List, Iterable, Set

from card_types import Card, Face, Suit, CARD_SCORE

_random_instance = random.Random()


def initialize_seed(seed):
    global _random_instance
    _random_instance = random.Random(seed)


def create_shuffled_deck(faces=Face) -> List[Card]:
    deck = []
    for f in faces:
        for s in Suit:
            deck.append(Card(s, f))
    _random_instance.shuffle(deck)
    return deck


def create_shuffled_4_player_hands() -> List[Set[Card]]:
    deck = create_shuffled_deck()
    return [set(deck[0:8]), set(deck[8:16]), set(deck[16:24]), set(deck[24:32])]


def create_shuffled_3_player_hands() -> List[Set[Card]]:
    deck = create_shuffled_deck(faces=[f for f in Face if f not in (Face.SIEBEN, Face.ACHT)])
    return [set(deck[0:8]), set(deck[8:16]), set(deck[16:24])]


def count_score(cards: Iterable[Card]):
    return sum(map(lambda card: CARD_SCORE[card.face], cards))


def create_cards() -> None:
    with open("cards.py", mode='w') as fo:
        for f in Face:
            for s in Suit:
                line = f"{s.name}_{f.name}".upper() + f" = Card({s}, {f})\n"
                fo.write(line)


# Generate the card deck as individual variables
if __name__ == '__main__':
    create_cards()
