from collections import namedtuple, defaultdict
from itertools import chain
import math

import numpy as np
import pygame

from gamestate import GameState, RED, GREEN, WHITE, BLUE, YELLOW, NUM_COLOURS, DECK, Card


pygame.init()
pygame.font.init()

font = pygame.font.SysFont(None, 35)
font.bold = True


ColourMap = {
    RED:           (239, 71, 111),
    GREEN:         (6, 214, 160),
    WHITE:         (255, 255, 255),
    BLUE:          (17, 138, 178),
    YELLOW:        (255, 209, 102),
    "BACKGROUND":  (240, 240, 240),
    "CARD":        (7, 59, 76),
    "DISCARD":     (200, 200, 200),
    "DRAW":        (100, 50, 50),
    "DRAWCOUNT":   (255, 150, 150),
    "SCORE":       (50, 50, 50)
}


class CardSprite():
    WIDTH = 70
    HEIGHT = 100

    @property
    def x(self):
        return self.rect.x

    @property
    def y(self):
        return self.rect.y
    
    @x.setter
    def x(self, value):
        self.rect.x = value

    @y.setter
    def y(self, value):
        self.rect.y = value

    def __init__(self, card, x=0, y=0):
        super().__init__()
        if card is None:
            self.colour = "DRAW"
            self.label = '?'
        else:
            self.colour, self.value , self.label = card.colour, card.value, card.label
            self.index = card.index
        
        self.back_colour = tuple(map(lambda x: 0.4*(x + 50), ColourMap[self.colour]))

        self.surf = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.rect = self.surf.get_rect()
        self.x, self.y = x, y

        self._render()

    def _render(self):
        self.surf.fill(ColourMap["BACKGROUND"])
        pygame.draw.rect(self.surf, self.back_colour, self.surf.get_rect(), border_radius=3)
        pygame.draw.rect(self.surf, (0, 0, 0), self.surf.get_rect(), 3, border_radius=3)

        font.underline = self.label in ('6', '9')
        shadow_offset = 2
        shadow_surf = font.render(self.label, True, (0, 0, 0))
        digit_surf = pygame.Surface(
            (shadow_surf.get_width() + shadow_offset, 
            shadow_surf.get_height() + shadow_offset)
        )
        digit_surf.fill(self.back_colour)
        digit_surf.blit(shadow_surf, (shadow_offset, shadow_offset))
        colour_surf = font.render(self.label, True, ColourMap[self.colour])
        digit_surf.blit(colour_surf, (0, 0))

        self.surf.blit(digit_surf, (5, 4))
        self.surf.blit(
            pygame.transform.rotate(digit_surf, 180), 
            (self.WIDTH - 5 - digit_surf.get_width(), self.HEIGHT - 4 - digit_surf.get_height())
        )



class DiscardSprite():
    WIDTH = CardSprite.WIDTH
    HEIGHT = CardSprite.HEIGHT

    def __init__(self, colour, x, y):
        self.colour = colour
        self.surf = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = x, y
        self._render()

    def _render(self):
        self.surf.fill(ColourMap["BACKGROUND"])
        pygame.draw.rect(self.surf, ColourMap["DISCARD"], self.surf.get_rect(), border_radius=12)


class DeckSprite():

    def __init__(self, x, y):
        self.surf = pygame.Surface((CardSprite.WIDTH, CardSprite.HEIGHT))
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = x, y
        self._render()

    def _render(self, value=44):
        self.surf.fill(ColourMap["BACKGROUND"])
        pygame.draw.rect(self.surf, ColourMap["DRAW"], self.surf.get_rect(), border_radius=10)
        pygame.draw.rect(self.surf, (0, 0, 0), self.surf.get_rect(), 3, border_radius=10)
        

Action = namedtuple("Action", ["card_index", "is_discard", "draw_choice"])
"""
(21, False, None)      :  Play card 21 from hand, draw from deck
(56, True, None)       :  Discard card 56 from hand, draw from deck
(3, True, Red) :  Discard card 3 from hand, draw from red pile
"""


class TableGUI:
    MOTION_FPS = 30
    STATIC_FPS = 8
    HAND_HEIGHT = CardSprite.HEIGHT / 2
    SCRN_W = 700
    SCRN_H = 900
    STACK_STEP = 30

    def __init__(self):
        self.screen = pygame.display.set_mode((self.SCRN_W, self.SCRN_H))
        self.clock = pygame.time.Clock()
        self.human_played_stacks = defaultdict(list)
        self.opponent_played_stacks = defaultdict(list)
        self.discard_piles = defaultdict(list)
        self.opponent_hand = []  # just used for dawing cards in motion
        self.selected_card_idx = None
        self.empty_slot = None
        self.human_scores, self.opponent_scores = np.zeros(5, dtype=int), np.zeros(5, dtype=int)

        self._create_background()

    def _hand_xy(self, idx=0):
        y = self.SCRN_H - self.HAND_HEIGHT
        x = ((idx - 4) * (CardSprite.WIDTH + 3)) + (self.SCRN_W / 2)
        return x, y


    def _create_background(self):
        self.surf = pygame.Surface((self.SCRN_W, self.SCRN_H))
        self.surf.fill(ColourMap["BACKGROUND"])

        self.discard_regions = {}
        self.all_discard_regions = None
        for colour in range(NUM_COLOURS):
            x = int((self.SCRN_W - DiscardSprite.WIDTH) / 2 + (colour - 1.5) * (DiscardSprite.WIDTH + 10))
            y = int((self.SCRN_H - self.HAND_HEIGHT - DiscardSprite.HEIGHT) / 2)
            sprite = DiscardSprite(colour, x, y)
            self.discard_regions[colour] = sprite.rect
            self.surf.blit(sprite.surf, sprite.rect)
            if self.all_discard_regions is None:
                self.all_discard_regions = pygame.Rect(sprite.rect)
            else:
                self.all_discard_regions.union_ip(sprite.rect)

        self.play_region = pygame.Rect(
            self.all_discard_regions.left,
            self.all_discard_regions.bottom + 5,
            self.all_discard_regions.width,
            (self.SCRN_W - DiscardSprite.WIDTH) // 2
        )

        self.deck_sprite = DeckSprite(15, int((self.SCRN_H - self.HAND_HEIGHT - CardSprite.HEIGHT) / 2))
        self.surf.blit(self.deck_sprite.surf, self.deck_sprite.rect)


    def set_state(self, hand, played=None, deck_size=44):
        self.deck_size = deck_size
        self.hand = []
        for i, card in enumerate(hand):
            x, y = self._hand_xy(i)
            self.hand.append(CardSprite(card, x=x, y=y))

        self._render()


    def _render(self):
        # Back
        self.screen.blit(self.surf, (0, 0))

        # Deck counter
        deck_size_surf = font.render(f"[{self.deck_size}]", True, ColourMap["DRAWCOUNT"])
        x = self.deck_sprite.rect.x + (self.deck_sprite.rect.width - deck_size_surf.get_width()) / 2
        y = self.deck_sprite.rect.y + (self.deck_sprite.rect.height - deck_size_surf.get_height()) / 2
        self.screen.blit(deck_size_surf, (x, y))

        # Score counters
        font.underline = False
        digit_surf = font.render(str(sum(self.human_scores)), True, ColourMap["SCORE"])
        x = self.deck_sprite.rect.centerx - digit_surf.get_width() / 2 
        y = self.deck_sprite.rect.bottom + (CardSprite.HEIGHT - digit_surf.get_height()) / 2 
        self.screen.blit(digit_surf, (x, y))
        digit_surf = font.render(str(sum(self.opponent_scores)), True, ColourMap["SCORE"])
        x = self.deck_sprite.rect.centerx - digit_surf.get_width() / 2 
        y = self.deck_sprite.rect.top - (CardSprite.HEIGHT + digit_surf.get_height()) / 2 
        self.screen.blit(digit_surf, (x, y))


        # Cards
        for stack in chain(self.human_played_stacks.values(), self.opponent_played_stacks.values()):
            for card in stack:
                self.screen.blit(card.surf, (card.x, card.y))
        for pile in self.discard_piles.values():
            if pile:
                card = pile[-1]
                self.screen.blit(card.surf, card.rect)
        for card in chain(self.hand, self.opponent_hand):
            if card is not None:
                self.screen.blit(card.surf, (card.x, card.y))


        pygame.display.flip()


    def _move_card(self, card, x, y, speed):
        speed /= self.MOTION_FPS
        while 1:
            self.clock.tick(self.MOTION_FPS)
            dx, dy = x - card.x, y - card.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < speed:
                card.x, card.y = x, y
                self._render()
                return
            card.x += dx * speed / distance
            card.y += dy * speed / distance
            self._render()


    def _select_card(self, card_idx):
        if card_idx == self.selected_card_idx:
            return
        if self.selected_card_idx is not None:
            self._unselect_card()
        self.selected_card_idx = card_idx
        card = self.hand[card_idx]
        self._move_card(card, card.x, self.SCRN_H - card.HEIGHT, speed=300)

    def _unselect_card(self):
        if self.selected_card_idx is not None:
            card = self.hand[self.selected_card_idx]
            x, y = self._hand_xy(self.selected_card_idx)
            self._move_card(card, x, y, speed=900)
            self.selected_card_idx = None

    def _discard_selected_card(self):
        card = self.hand[self.selected_card_idx]
        self.empty_slot = self.selected_card_idx
        dst = self.discard_regions[card.colour]
        self._move_card(card, dst.x, dst.y, speed=800)
        self.discard_piles[card.colour].append(card)
        self.hand[self.selected_card_idx] = None
        self.selected_card_idx = None

    def _can_play_selected(self):
        card = self.hand[self.selected_card_idx]
        stack = self.human_played_stacks[card.colour]
        return not stack or stack[-1].value <= card.value

    def _play_selected_card(self):
        card = self.hand[self.selected_card_idx]
        self.empty_slot = self.selected_card_idx
        stack = self.human_played_stacks[card.colour]
        x = self.discard_regions[card.colour].x
        y = self.play_region.top + len(stack) * self.STACK_STEP
        self._move_card(card, x, y, speed=800)
        stack.append(card)
        self.hand[self.selected_card_idx] = None
        self.selected_card_idx = None

    def _draw_from_discard(self, colour):
        card = self.discard_piles[colour].pop()
        self.hand[self.empty_slot] = card
        x, y = self._hand_xy(self.empty_slot)
        self._move_card(card, x, y, speed=800)
        self.empty_slot = None

    def draw_from_deck(self, card_spec):
        self.deck_size -= 1
        self._render()

        card = CardSprite(
            card_spec, 
            self.deck_sprite.rect.x, 
            self.deck_sprite.rect.y
        )
        self.hand[self.empty_slot] = card
        x, y = self._hand_xy(self.empty_slot)
        self._move_card(card, x, y, speed=1000)
        self.empty_slot = None


    def _wait_for_click(self):
        pygame.event.clear()
        while 1:
            self.clock.tick(self.STATIC_FPS)
            self._render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return ("Quit", None)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return pygame.mouse.get_pos()

    def get_play(self):
        while 1:
            click_pos = self._wait_for_click()

            for card_idx, card in enumerate(self.hand):
                if card is None:
                    continue
                if card.rect.collidepoint(click_pos):
                    self._select_card(card_idx)
                    break
            else:
                if self.selected_card_idx is not None:

                    if self.all_discard_regions.collidepoint(click_pos):
                        card_id = self.hand[self.selected_card_idx].index
                        self._discard_selected_card()
                        return card_id, True

                    if self.play_region.collidepoint(click_pos) and self._can_play_selected():
                        card_id = self.hand[self.selected_card_idx].index
                        self._play_selected_card()
                        return card_id, False

                self._unselect_card()


    def get_draw(self):
        while 1:
            click_pos = self._wait_for_click()

            for colour in range(NUM_COLOURS):
                if self.discard_regions[colour].collidepoint(click_pos):
                    if self.discard_piles[colour]:
                        self._draw_from_discard(colour)
                        return colour

            if self.deck_sprite.rect.collidepoint(click_pos):
                return DECK


    def opponent_play(self, card_choice, is_discard):
        card = CardSprite(
            Card(card_choice),
            x=self.SCRN_W // 2,
            y=-CardSprite.HEIGHT
        )

        if is_discard:
            pile = self.discard_regions[card.colour]
            x, y = pile.x, pile.y

        else:
            stack = self.opponent_played_stacks[card.colour]
            x = self.discard_regions[card.colour].x
            y = self.all_discard_regions.top - 5 - CardSprite.HEIGHT - len(stack) * self.STACK_STEP
            stack.append(card)

        self.opponent_hand.append(card)
        self._move_card(card, x, y, speed=1000)
        self.opponent_hand.pop()

        if is_discard:
            self.discard_piles[card.colour].append(card)


    def opponent_draw(self, source_choice, drawn_card):
        if source_choice == DECK:
            self.deck_size -= 1
            card = CardSprite(None, x=self.deck_sprite.rect.x, y=self.deck_sprite.rect.y)
        else:
            card = self.discard_piles[drawn_card.colour].pop()

        self.opponent_hand.append(card)
        self._move_card(card,
            x=self.SCRN_W // 2,
            y=-CardSprite.HEIGHT,
            speed=1000
        )
        self.opponent_hand.pop()


    def set_scores(self, human_scores, opponent_scores):
        self.human_scores, self.opponent_scores = human_scores, opponent_scores


