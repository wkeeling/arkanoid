import pygame

from arkanoid.util import load_png


class TopEdge(pygame.sprite.Sprite):
    """The top edge of the game area."""

    def __init__(self):
        super().__init__()

        self.image, self.rect = load_png('top.png')
        self.visible = True

    def update(self):
        pass


class SideEdge(pygame.sprite.Sprite):
    """The side edge of the game area."""

    def __init__(self):
        super().__init__()

        self.image, self.rect = load_png('edge.png')
        self.visible = True

    def update(self):
        pass
