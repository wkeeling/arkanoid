import logging
import sys

import pygame

from arkanoid.sprites import Ball
from arkanoid.sprites import Paddle
from arkanoid.utils import load_png


LOG = logging.getLogger(__name__)


# The speed the game runs at in FPS.
GAME_SPEED = 60
# The dimensions of the main game window in pixels.
DISPLAY_SIZE = 600, 650
# The title of the main window.
DISPLAY_CAPTION = 'Arkanoid'
# The angle the ball initially moves off the paddle, in radians.
BALL_START_ANGLE_RAD = 5.0
# The speed that the ball will always try to arrive at.
BALL_BASE_SPEED = 8  # pixels per-frame
# The max speed of the ball, prevents a runaway speed when lots of rapid
# collisions.
BALL_MAX_SPEED = 15  # pixels per-frame
# Per-frame rate at which ball is brought back to base speed.
BALL_SPEED_NORMALISATION_RATE = 0.02
# Increase in speed caused by colliding with a brick.
BRICK_SPEED_ADJUST = 0.5
# Increase in speed caused by colliding with a wall.
WALL_SPEED_ADJUST = 0.2
# The speed the paddle moves.
PADDLE_SPEED = 10


class Arkanoid:

    def main_loop(self):
        # Initialise the screen.
        pygame.init()
        screen = self._create_screen()

        # Create the background
        background = self._create_background(screen)

        # Create the edges of the game area.
        left, right, top = self._create_edges(background)

        # Blit the background to the screen.
        screen.blit(background, (0, 0))

        # Initialise the sprites.
        paddle = Paddle(left_offset=left.width,
                        right_offset=right.width,
                        bottom_offset=50,
                        speed=PADDLE_SPEED)
        paddlesprite = pygame.sprite.RenderPlain(paddle)

        ball = Ball(start_pos=paddle.rect.midtop,
                    start_angle=BALL_START_ANGLE_RAD,
                    base_speed=BALL_BASE_SPEED,
                    max_speed=BALL_MAX_SPEED,
                    normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                    off_screen_callback=self._off_screen)

        # Let the ball know about the objects it might collide with.
        ball.add_collidable_object(left, speed_adjust=WALL_SPEED_ADJUST)
        ball.add_collidable_object(right, speed_adjust=WALL_SPEED_ADJUST)
        ball.add_collidable_object(top, speed_adjust=WALL_SPEED_ADJUST)
        ball.add_collidable_object(paddle, bounce_strategy=paddle.bounce_strategy)

        # Create the bricks.
        bricks = self._create_bricks(screen)

        def on_brick_collide(brick):
            ball.remove_collidable_object(brick)
            screen.blit(background, brick, brick)

        for brick in bricks:
            # Make the ball aware of the bricks it might collide with. Every
            # brick collision slightly increases the speed of the ball.
            ball.add_collidable_object(brick, speed_adjust=BRICK_SPEED_ADJUST,
                                       on_collide=on_brick_collide)

        ballsprite = pygame.sprite.RenderPlain(ball)

        # Initialise the clock.
        clock = pygame.time.Clock()

        running = True

        while running:
            # Clock runs at 60 fps.
            clock.tick(GAME_SPEED)

            # Monitor for key presses.
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
                        paddle.stop()

            # Erase the previous location of the sprites.
            paddlesprite.clear(screen, background)
            ballsprite.clear(screen, background)

            # Update the state of the sprites and redraw them.
            paddlesprite.update()
            paddlesprite.draw(screen)
            ballsprite.update()
            ballsprite.draw(screen)

            # Display all updates.
            pygame.display.flip()

        LOG.debug('Exiting')

    def _create_screen(self):
        screen = pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        return screen

    def _create_background(self, screen):
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))
        return background

    def _create_edges(self, background):
        edge, _ = load_png('edge.png')
        left_rect = background.blit(edge, (0, 0))
        right_rect = background.blit(edge, (DISPLAY_SIZE[0] - edge.get_width(), 0))
        top_edge, _ = load_png('top.png')
        top_rect = background.blit(top_edge, (edge.get_width(), 0))
        return left_rect, right_rect, top_rect

    def _create_bricks(self, screen):
        # TODO: this will be moved into each level subclass called by __init__()
        # to populate a level.bricks attribute. Adjust pixel dimensions for better
        # graphics.
        bricks = []
        colours = 'green', 'blue', 'yellow', 'red', 'grey'
        top = 200

        for colour in colours:
            brick, _ = load_png('brick_{}.png'.format(colour))
            left = 15
            for i in range(13):
                # 13 bricks are added horizontally
                rect = screen.blit(brick, (left, top))
                left += 44
                bricks.append(rect)
            top -= 22

        return bricks

    def _off_screen(self):
        sys.exit()

