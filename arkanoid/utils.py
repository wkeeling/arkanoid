import functools
import os

import pygame


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


@functools.lru_cache()
def font(name, size):
    """Get the named font at given size. This will load the font if it hasn't
    previously been loaded.

    Args:
        name:
            The filename of the font.
        size:
            The size of the font.
    """
    return pygame.font.Font(
        os.path.join(os.path.dirname(__file__), 'data', 'fonts', name), size)
