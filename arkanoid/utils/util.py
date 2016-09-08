import functools
import os

import pygame


HIGH_SCORE_FILE = os.path.join(os.path.expanduser('~'), '.arkanoid')


def load_png(filename):
    """Load a png image with the specified filename from the
    data/graphics directory and return it and its Rect.

    Args:
        filename:
            The filename of the image, with or without the '.png' extension.
    Returns:
        A 2-tuple of the image and its Rect.
    Raises:
        FileNotFoundError if the image filename was not found.
    """
    if not filename.lower().endswith('.png'):
        filename = '{}.png'.format(filename)
    fullpath = os.path.join(os.path.dirname(__file__), '..', 'data',
                            'graphics', filename)
    if not os.path.exists(fullpath):
        raise FileNotFoundError('File not found: {}'.format(fullpath))

    image = pygame.image.load(fullpath)
    if image.get_alpha is None:
        image = image.convert()
    else:
        image = image.convert_alpha()

    return image, image.get_rect()


def load_png_sequence(filename_prefix):
    """Load a sequence of png images with the specified filename from the
    data/graphics directory.

    Each png filename in the sequence will be formed by appending an
    incrementing number, starting at 1, followed by the .png extension. The
    png files will then be loaded for each sequence number until a file
    cannot be found, at which point loading will stop and a list of
    the files will be returned.

    For example, if the filename prefix is 'paddle_wide' then a filename of
    'paddle_wide_1.png' will attempt to be loaded, followed by
    'paddle_wide_2.png' etc. until a file cannot be found.

    Args:
        filename_prefix:
            The beginning of the png filename of each file in the sequence.
    Returns:
        A list of 2-tuples of image/rect.
    """
    count, sequence = 1, []

    while True:
        filename = '%s_%s.png' % (filename_prefix, count)
        try:
            sequence.append(load_png(filename))
        except FileNotFoundError:
            # End of sequence.
            break
        else:
            count += 1

    return sequence


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
        os.path.join(os.path.dirname(__file__), '..', 'data', 'fonts', name),
        size)


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


def save_high_score(value):
    """Save the high score value.

    The high score is saved in a file called .highscore in the current user's
    home directory.

    Args:
         value:
            The high score.
    """
    with open(HIGH_SCORE_FILE, 'w') as file:
        file.write(str(value))


def load_high_score():
    """Load the current high score value.

    The high score is loaded from a file called .highscore in the current
    user's home directory.

    Returns:
        The high score or zero if no previous high score (the .highscore file
        does not exist).
    """
    if not os.path.exists(HIGH_SCORE_FILE):
        # Explicitly test for file existence rather than trying to catch
        # an IOError on open(), as the IOError might indicate something
        # other than file not found (although unlikely).
        return 0

    with open(HIGH_SCORE_FILE) as file:
        return int(file.read().strip())
