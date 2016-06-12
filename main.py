import logging

from arkanoid.game import Arkanoid


logging.basicConfig()
LOG = logging.getLogger('arkanoid')
LOG.setLevel(logging.DEBUG)


if __name__ == '__main__':
    arkanoid = Arkanoid()
    arkanoid.main_loop()
