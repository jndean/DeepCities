import pygame


pygame.init()
pygame.font.init()
card_font = pygame.font.SysFont(None, 40)
card_font.bold = True
card_font.underline = True


class Colour:
    RED = (239, 71, 111)
    GREEN = (6, 214, 160)
    WHITE = (255, 255, 255)
    BLUE = (17, 138, 178)
    YELLOW = (255, 209, 102)
    BACKGROUND = (255, 255, 255)
    CARD = (7, 59, 76)


class Card(pygame.sprite.Sprite):

    def __init__(self, colour, value, x=0, y=0, on_table=True):
        super().__init__()
        self.on_table = on_table
        self.colour, self.value = colour, value
        self.x, self.y = x, y
        
        self.width, self.height = (80, 120) if on_table else (150, 200)

        self.surf = pygame.Surface((self.width, self.height))
        self.rect = self.surf.get_rect()

        self._render()

    def _render(self):
        self.surf.fill(Colour.BACKGROUND)
        pygame.draw.rect(self.surf, Colour.CARD, self.rect, border_radius=10)
        pygame.draw.rect(self.surf, (0, 0, 0), self.rect, 2, border_radius=10)
        digit_surf = card_font.render(str(self.value), True, (0, 0, 0), Colour.CARD)
        self.surf.blit(digit_surf, (7, 7))
        digit_surf = card_font.render(str(self.value), True, self.colour)
        self.surf.blit(digit_surf, (5, 5))





if __name__ == "__main__":


    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    


    card = Card(Colour.RED, "X", x=400, y=400)

    running = True
    while running:

        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill the background with white
        screen.fill(Colour.BACKGROUND)

        screen.blit(card.surf, (card.x, card.y))

        card.x += 1

        pygame.display.flip()

    pygame.quit()
