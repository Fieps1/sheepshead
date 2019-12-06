import numpy as np

from deck import *


class Sauspiel:

    NON_TRUMP_ORDER = [SAU, ZEHN, KOENIG, NEUN, ACHT, SIEBEN]
    NON_TRUMP_FACE_RANKS = {face: power + 100 for power, face in enumerate(NON_TRUMP_ORDER)}

    TRUMP_ORDER = [Card(s, OBER) for s in Suit] \
        + [Card(s, UNTER) for s in Suit] \
        + [Card(HERZ, f) for f in NON_TRUMP_ORDER]
    TRUMP_CARD_RANKS = {card: power for power, card in enumerate(TRUMP_ORDER)}

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

    def allowed_cards(self, layed_out_cards: List[Card], player_cards: List[Card]):
        if len(layed_out_cards) == 0:
            return player_cards

        first_card = layed_out_cards[0]

        if first_card in self.TRUMP_CARD_RANKS:
            matching_cards = [c for c in player_cards if c in self.TRUMP_CARD_RANKS]
        else:
            matching_cards = [c for c in player_cards if c.suit == first_card.suit and c.face in self.NON_TRUMP_FACE_RANKS]

        if len(matching_cards) == 0:
            return player_cards
        else:
            return matching_cards


if __name__ == '__main__':

    deck = create_shuffled_deck()

    sauspiel = Sauspiel()

    print(sauspiel.TRUMP_ORDER)
