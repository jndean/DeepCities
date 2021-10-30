from collections import namedtuple, defaultdict
import math

import pygame

from gamestate import GameState, Colour


pygame.init()
pygame.font.init()

font = pygame.font.SysFont(None, 35)
font.bold = True


ColourMap = {
    Colour.RED:    (239, 71, 111),
    Colour.GREEN:  (6, 214, 160),
    Colour.WHITE:  (255, 255, 255),
    Colour.BLUE:   (17, 138, 178),
    Colour.YELLOW: (255, 209, 102),
    "BACKGROUND":  (240, 240, 240),
    "CARD":        (7, 59, 76),
    "DISCARD":     (200, 200, 200),
    "DRAW":        (100, 50, 50),
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

    def __init__(self, colour, value, x=0, y=0):
        super().__init__()
        self.colour, self.value = colour, value
        
        self.back_colour = tuple(map(lambda x: 0.4*(x + 50), ColourMap[colour]))

        self.surf = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.rect = self.surf.get_rect()
        self.x, self.y = x, y

        self._render()

    def _render(self):
        self.surf.fill(ColourMap["BACKGROUND"])
        pygame.draw.rect(self.surf, self.back_colour, self.surf.get_rect(), border_radius=3)
        pygame.draw.rect(self.surf, (0, 0, 0), self.surf.get_rect(), 3, border_radius=3)

        font.underline = self.value in (6, 9)
        shadow_offset = 2
        digit = "X" if self.value == 0 else str(self.value)
        shadow_surf = font.render(digit, True, (0, 0, 0))
        digit_surf = pygame.Surface(
            (shadow_surf.get_width() + shadow_offset, 
            shadow_surf.get_height() + shadow_offset)
        )
        digit_surf.fill(self.back_colour)
        digit_surf.blit(shadow_surf, (shadow_offset, shadow_offset))
        colour_surf = font.render(digit, True, ColourMap[self.colour])
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
        


Input = namedtuple("Input", ["action", "choice"])
"""
["Play", 3]           # Play card 3 from hand
["Discard", 0]        # Discard card 0 from hand
["Draw", None]        # Draw from deck
["Draw", Colour.RED]  # Draw from red discard pile
["Quit", None]        # Quit
"""

class TableGUI:
    MOTION_FPS = 60
    STATIC_FPS = 10
    HAND_HEIGHT = CardSprite.HEIGHT / 2
    SCRN_W = 700
    SCRN_H = 900

    def __init__(self):
        self.screen = pygame.display.set_mode((self.SCRN_W, self.SCRN_H))
        self.clock = pygame.time.Clock()
        self.human_played_stacks = defaultdict(list)
        self.machine_played_stacks = defaultdict(list)
        self.discard_piles = defaultdict(list)
        self.selected_card_idx = None

        self._create_background()

    def _create_background(self):
        self.surf = pygame.Surface((self.SCRN_W, self.SCRN_H))
        self.surf.fill(ColourMap["BACKGROUND"])

        self.discard_regions = {}
        self.all_discard_regions = None
        for i, colour in enumerate(Colour):
            x = int((self.SCRN_W - DiscardSprite.WIDTH) / 2 + (i - 1.5) * (DiscardSprite.WIDTH + 10))
            y = int((self.SCRN_H - self.HAND_HEIGHT - DiscardSprite.HEIGHT) / 2)
            sprite = DiscardSprite(colour, x, y)
            self.discard_regions[colour] = sprite
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


    def set_state(self, hand, played=None):
        self.hand = []
        for i, card in enumerate(hand):
            y = self.SCRN_H - self.HAND_HEIGHT
            x = ((i - 4) * (CardSprite.WIDTH + 3)) + (self.SCRN_W / 2)
            self.hand.append(CardSprite(card.colour, card.value, x=x, y=y))

        self._render()


    def _render(self):
        self.screen.blit(self.surf, (0, 0))

        for stack in self.human_played_stacks.values():
            for card in stack:
                self.screen.blit(card.surf, (card.x, card.y))
        for pile in self.discard_piles.values():
            if pile:
                card = pile[-1]
                self.screen.blit(card.surf, card.rect)
        for card in self.hand:
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
            self._move_card(card, card.x, self.SCRN_H - self.HAND_HEIGHT, speed=900)
            self.selected_card_idx = None

    def _discard_selected_card(self):
        card = self.hand[self.selected_card_idx]
        dst = self.discard_regions[card.colour].rect
        self._move_card(card, dst.x, dst.y, speed=1000)
        self.discard_piles[card.colour].append(card)
        self.hand[self.selected_card_idx] = None
        self.selected_card_idx = None

    def _can_play_selected(self):
        card = self.hand[self.selected_card_idx]
        stack = self.human_played_stacks[card.colour]
        return not stack or card.value >= stack[-1].value

    def _play_selected_card(self):
        card = self.hand[self.selected_card_idx]
        stack = self.human_played_stacks[card.colour]
        x = self.discard_regions[card.colour].rect.x
        y = self.play_region.top + len(stack) * 30
        self._move_card(card, x, y, speed=800)
        stack.append(card)
        self.hand[self.selected_card_idx] = None
        self.selected_card_idx = None

    def _wait_for_click(self):
        pygame.event.clear()
        while 1:
            self.clock.tick(self.STATIC_FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return Input("Quit", None)
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
                        ret = Input("Discard", self.selected_card_idx)
                        self._discard_selected_card()
                        return ret
                    if self.play_region.collidepoint(click_pos) and self._can_play_selected():
                        ret = Input("Play", self.selected_card_idx)
                        self._play_selected_card()
                        return ret

                self._unselect_card()


if __name__ == "__main__":


    state = GameState()
    state.init_random_game()
    table = TableGUI()
    table.start(state.hands[0])

    table.get_input()
    



   
