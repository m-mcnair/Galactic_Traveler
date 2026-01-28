import sys
import pygame

from src.settings import Settings
from src.states import Game


def main():
    pygame.init()
    pygame.display.set_caption("Galactic Traveler")
    settings = Settings()

    screen = pygame.display.set_mode((settings.W, settings.H))
    clock = pygame.time.Clock()

    game = Game(settings)

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)
        game.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
