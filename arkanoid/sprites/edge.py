import pygame

from arkanoid.util import load_png


class TopEdge(pygame.sprite.Sprite):
    """The top edge of the game area."""

    def __init__(self):
        super().__init__()

        self.image, self.rect = load_png('top_edge')
        self.visible = True

    def update(self):
        pass


class SideEdge(pygame.sprite.Sprite):
    """The side edge of the game area."""

    def __init__(self, side):
        """Initialise a new SideEdge specifying which side - either 'left'
        or 'right'.

        Args:
            side:
                The side - either 'left' or 'right'.
        """
        if side not in ('left', 'right'):
            raise AttributeError("Side must be either 'left' or 'right'")

        super().__init__()

        self.image, self.rect = load_png('%s_edge' % side)
        self.visible = True

    def update(self):
        pass
