"""
Entry point module for running Arkanoid.
"""
import math
import os
import logging

import pygame

logging.basicConfig()
LOG = logging.getLogger('arkanoid')
LOG.setLevel(logging.DEBUG)

DISPLAY_SIZE = 600, 650
DISPLAY_CAPTION = 'Arkanoid'
BALL_START_ANGLE_RAD = 5.5
BALL_START_SPEED = 8


class Paddle(pygame.sprite.Sprite):
    """The movable paddle used to control the ball."""

    # TODO: Need a "bonus collision action" which can be added to the paddle
    # and the paddle invokes the callback when a bonus is struck. This can
    # be less generic than the "collidable object" concept the ball has,
    # because the bonuses are the only thing to strike the paddle (apart from
    # the ball).

    def __init__(self):
        super(Paddle, self).__init__()
        self.image, self.rect = load_png('paddle.png')
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self.rect.midbottom = self._area.midbottom
        self.rect.top -= 50
        self._offset = 0
        self._speed = 10

    def update(self):
        # Continuously move the paddle when the offset is non-zero.
        newpos = self.rect.move(self._offset, 0)
        if self._area.contains(newpos):
            # But only update the position of the paddle if it's within
            # the screen area.
            self.rect = newpos

    def move_left(self):
        # Set the offset to negative to move left.
        self._offset = -self._speed

    def move_right(self):
        # A positive offset to move right.
        self._offset = self._speed

    def stop(self):
        self._offset = 0

    @staticmethod
    def ball_bounce_strategy(paddle_rect, ball_rect):
        """The strategy used to calculate the angle that the ball bounces
        off the paddle. The angle of bounce is dependent upon where the
        ball strikes the paddle.

        Note: this function is not tied to the Paddle class but we house it
        here as it seems a reasonable place to keep it.

        Args:
            paddle_rect:
                The Rect of the paddle.
            ball_rect:
                The Rect of the ball.

        Returns:
            The angle of bounce in radians.
        """
        # TODO: this may need to return a tuple of (angle, speed_level) where
        # speed_level is say, NORMAL or FAST, and the Ball will then
        # interpret that by modifying the actual speed appropriately.


class Ball(pygame.sprite.Sprite):
    """The ball that bounces around the screen."""

    def __init__(self, start_pos, start_angle, start_speed,
                 off_screen_callback=None):
        """
        Initialise a new ball.

        Args:
            start_pos:
                The starting position of the ball (coordinates).
            start_angle:
                The starting angle of the ball in radians taken against the
                x axis.
            start_speed:
                The starting speed of the ball.
            off_screen_callback:
                A no-args callable that will be called if the ball goes off
                the edge of the screen.
        """
        super(Ball, self).__init__()
        self._angle = start_angle
        self._speed = start_speed
        self.image, self.rect = load_png('ball.png')
        self.rect.midbottom = start_pos
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()
        self._collidable_objects = []
        self._off_screen_callback = off_screen_callback

    def add_collidable_object(self, obj, bounce_strategy=None,
                              on_collide=None):
        """Add an object that the ball could collide with. The object should
        be a Rect for static objects, or a Sprite for animated objects.

        Args:
            obj:
                The collidable object. A Rect for static objects,
                or a Sprite for animated objects.
            bounce_strategy:
                Optional callable that determines how the ball should bounce
                when it collides with the object.
            on_collide:
                Optional callable that will be called when a collision occurs.
        """
        self._collidable_objects.append((obj, bounce_strategy, on_collide))

    def remove_collidable_object(self, obj):
        """Remove an object so that the ball can no longer collide with it.

        Args:
            obj:
                The collidable object to remove - either the Rect or Sprite.
        """
        self._collidable_objects = [(col, strat, cbk) for col, strat, cbk in
                                    self._collidable_objects if col == obj]

    def update(self):
        # Get the new position of the ball.
        self.rect = self._calc_new_pos()

        if self._area.contains(self.rect):
            # The ball is still on the screen.
            # Find out if the ball has collided with anything.
            collidable_rects = self._get_collidable_rects()
            index = self.rect.collidelist(collidable_rects)

            if index > -1:
                # There's been a collision - find out with what.
                rect = collidable_rects[index]

                # Work out the new angle of the ball based on what it hit.
                _, bounce_strat, callback = self._collidable_objects[index]
                if bounce_strat:
                    # Use the bounce strategy that has been supplied to
                    # work out the angle.
                    self._angle = bounce_strat(rect, self.rect)
                else:
                    # Use the default calculation for the angle.
                    self._angle = self._calc_new_angle(rect)

                if callback:
                    # Notify the listener associated with this object
                    # that the object has been struck by the ball.
                    callback(rect, self.rect)
        else:
            # Ball has gone off the screen.
            # Invoke the callback if we have one.
            if self._off_screen_callback:
                self._off_screen_callback()

    def _get_collidable_rects(self):
        """Resolve the Rects from the collidable objects we have."""
        collidable_rects = []

        for obj, _, _ in self._collidable_objects:
            try:
                collidable_rects.append(obj.rect)
            except AttributeError:
                collidable_rects.append(obj)

        return collidable_rects

        # if not self._area.contains(new_pos):
        #     LOG.info('Off the screen: %s, %s', new_pos, self._area)
        #     # The ball is partially out of the screen, so we need to change
        #     # the angle in order to trigger a bounce.
        #     tl_out = not self._area.collidepoint(new_pos.topleft)
        #     tr_out = not self._area.collidepoint(new_pos.topright)
        #     bl_out = not self._area.collidepoint(new_pos.bottomleft)
        #     br_out = not self._area.collidepoint(new_pos.bottomright)
        #     top_out = tl_out and tr_out
        #     bottom_out = bl_out and br_out
        #
        #     if top_out:
        #         if bl_out or br_out:
        #             # The ball has gone out of a top corner, so bounce
        #             # it back in the opposite direction
        #             self._angle = self._angle + math.pi
        #         else:
        #             # Ball has hit the top
        #             self._angle = -self._angle
        #     elif bottom_out:
        #         # TODO: This represents an end of life
        #         if tl_out or tr_out:
        #             # The ball has gone out of a bottom corner, so bounce
        #             # it back in the opposite direction
        #             self._angle = self._angle + math.pi
        #         else:
        #             # Ball has hit the bottom
        #             self._angle = -self._angle
        #     else:
        #         # Ball has hit the side
        #         self._angle = math.pi - self._angle

    def _calc_new_pos(self):
        offset_x = self._speed * math.cos(self._angle)
        offset_y = self._speed * math.sin(self._angle)

        return self.rect.move(offset_x, offset_y)

    def _calc_new_angle(self, object_rect):
        # TODO: below is the default bounce strategy
        # strategy(ball_rect, object_rect)  ==>  angle
        tl_col = object_rect.collidepoint(self.rect.topleft)
        tr_col = object_rect.collidepoint(self.rect.topright)
        bl_col = object_rect.collidepoint(self.rect.bottomleft)
        br_col = object_rect.collidepoint(self.rect.bottomright)
        points = tl_col, tr_col, bl_col, br_col
        top_col = tl_col and tr_col
        bottom_col = bl_col and br_col

        if top_col or bottom_col:
            # Top of the ball has collided with the bottom of an object,
            # or bottom of the ball has collided with the top of an object.
            angle = -self._angle
        elif any(points) and not any(points):
            # Ball has hit the corner of an object. Bounce it back in the
            # opposite direction.
            angle = self._angle + math.pi
        else:
            # Ball has hit the side of an object.
            angle = math.pi - self._angle

        return angle


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
    # TODO: doc on initialisers

    # Initialise the screen
    pygame.init()
    screen = create_screen()

    # Create the background
    background = create_background(screen)

    # Create the edges of the game area
    left, right, top = create_edges(background)

    # Initialise the sprites
    paddle = Paddle()
    paddlesprite = pygame.sprite.RenderPlain(paddle)
    ball = Ball(start_pos=paddle.rect.midtop,
                start_angle=BALL_START_ANGLE_RAD,
                start_speed=BALL_START_SPEED,
                off_screen_callback=off_screen)
    # Let the ball know about the objects it might collide with
    ball.add_collidable_object(left)
    ball.add_collidable_object(right)
    ball.add_collidable_object(top)
    ball.add_collidable_object(paddle)
    ballsprite = pygame.sprite.RenderPlain(ball)

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
                    paddle.stop()

        # Erase the previous location of the sprites
        paddlesprite.clear(screen, background)
        ballsprite.clear(screen, background)

        # Update and redraw the sprites
        paddlesprite.update()
        paddlesprite.draw(screen)
        ballsprite.update()
        ballsprite.draw(screen)

        pygame.display.flip()

    LOG.info('Exiting')


def create_screen():
    screen = pygame.display.set_mode(DISPLAY_SIZE)
    pygame.display.set_caption(DISPLAY_CAPTION)
    pygame.mouse.set_visible(False)
    return screen


def create_background(screen):
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    return background


def create_edges(background):
    edge, _ = load_png('edge.png')
    left_rect = background.blit(edge, (0, 0))
    right_rect = background.blit(edge, (DISPLAY_SIZE[0] - edge.get_width(), 0))
    top_edge, _ = load_png('top.png')
    top_rect = background.blit(top_edge, (edge.get_width(), 0))
    return left_rect, right_rect, top_rect


def off_screen():
    LOG.debug('Ball gone off the screen!')


if __name__ == '__main__':
    run_game()
