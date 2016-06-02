"""
Entry point module for running Arkanoid.
"""
import os
import logging

import pygame

logging.basicConfig()
LOG = logging.getLogger('arkanoid')
LOG.setLevel(logging.DEBUG)


class Paddle(pygame.sprite.Sprite):
    """The movable paddle used to control the ball."""

    def __init__(self):
        super(Paddle, self).__init__()
        self.image, self.rect = load_png('paddle.png')
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self.rect.midbottom = self._area.midbottom
        self.rect.top -= 50
        self._move_by = 0
        self._speed = 10

    def update(self):
        newpos = self.rect.move(self._move_by, 0)
        if self._area.contains(newpos):
            self.rect = newpos

    def move_left(self):
        self._move_by -= self._speed

    def move_right(self):
        self._move_by += self._speed

    def stopped(self):
        self._move_by = 0


def load_png(filename):
    """Load a png image with the specified filename from the
    data/graphics directory and return it and its rect.

    Args:
        filename:
            The filename of the image.
    Returns:
        A 2-tuple of the image and its rect.
    """
    image = pygame.image.load(
        os.path.join('data', 'graphics', filename))
    if image.get_alpha is None:
        image = image.convert()
    else:
        image = image.convert_alpha()
    return image, image.get_rect()


def run_game():
    # TODO: turn this into an Arkenoid class with a main_loop()

    # Initialise the screen
    pygame.init()
    screen = create_screen()

    # Fill the background
    background = create_background(screen)

    # Initialise the sprites
    paddle = Paddle()
    paddlesprite = pygame.sprite.RenderPlain(paddle)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Initialise the clock
    clock = pygame.time.Clock()

    running = True

    while running:
        # Clock runs at 60 fps
        clock.tick(60)

        # Monitor for key presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    paddle.move_left()
                elif event.key == pygame.K_RIGHT:
                    paddle.move_right()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    paddle.stopped()

        # Erase the previous location of the sprites
        screen.blit(background, paddle.rect, paddle.rect)

        # Update the new location of the sprites
        paddlesprite.update()
        paddlesprite.draw(screen)

        pygame.display.flip()

    LOG.info('Exiting')


def create_screen():
    screen = pygame.display.set_mode((600, 650))
    pygame.display.set_caption('Arkanoid')
    pygame.mouse.set_visible(False)
    return screen


def create_background(screen):
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    return background


if __name__ == '__main__':
    run_game()
