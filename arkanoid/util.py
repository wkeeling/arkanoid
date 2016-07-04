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
    Raises:
        FileNotFoundError if the image filename was not found.
    """
    q_filename = os.path.join(os.path.dirname(__file__), 'data', 'graphics', filename)
    if not os.path.exists(q_filename):
        raise FileNotFoundError('File not found: {}'.format(q_filename))
    image = pygame.image.load(q_filename)
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


def h_centre_pos(surface):
    """Get the left coordinate needed to centre the supplied surface
    horizontally in the centre of the screen.

    Args:
        surface:
            The surface to get the left coordinate for.

    Returns:
        The left coordinate which can be used to centre the surface
        horizontally in the screen.
    """
    screen = pygame.display.get_surface()
    return (screen.get_width() / 2) - (surface.get_width() / 2)
