import functools
import os

import pygame


# Initialise the clock.
clock = pygame.time.Clock()


@functools.lru_cache()
def load_png(filename):
    """Load a png image with the specified filename from the
    data/graphics directory and return it and its Rect.

    Args:
        filename:
            The filename of the image.
    Returns:
        A 2-tuple of the image and its Rect.
    """
    image = pygame.image.load(
        os.path.join(os.path.dirname(__file__), 'data', 'graphics', filename))
    if image.get_alpha is None:
        image = image.convert()
    else:
        image = image.convert_alpha()
    return image, image.get_rect()
