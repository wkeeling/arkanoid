from unittest.case import TestCase
from unittest.mock import (call,
                           Mock,
                           patch)

import pygame

from arkanoid.sprites.ball import (Ball,
                                   RANDOM_RANGE)


class TestBall(TestCase):

    def _configure_mocks(self, mock_pygame, mock_load_png, offscreen=True):
        (mock_image,
         mock_screen,
         mock_area,
         mock_sprite) = Mock(), Mock(), Mock(), Mock()

        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = offscreen

        return mock_sprite

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calculate_new_position(self, mock_pygame, mock_load_png):
        self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.36, 8)
        ball.update()

        # Offset x: -5.678340450896964
        # Offset y: 5.63528612616141

        self.assertAlmostEqual(ball.rect.x, 95.0)
        self.assertAlmostEqual(ball.rect.y, 105.0)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_invoke_offscreen_callback(self, mock_pygame,
                                       mock_load_png):
        self._configure_mocks(mock_pygame, mock_load_png, offscreen=False)

        mock_pygame.sprite.spritecollide.return_value = []
        mock_offscreen_callback = Mock()

        ball = Ball((100, 100), 2.36, 8,
                    off_screen_callback=mock_offscreen_callback)

        ball.update()

        mock_offscreen_callback.assert_called_with(ball)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_speed_normalised_down_when_no_collision(self, mock_pygame,
                                                     mock_load_png):
        self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.36, 8, normalisation_rate=0.03)
        ball.speed = 12  # Increase the speed above the base speed.

        ball.update()

        self.assertEqual(ball.speed, 11.97)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_speed_normalised_up_when_no_collision(self, mock_pygame,
                                                   mock_load_png):
        self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.36, 8, normalisation_rate=0.03)
        ball.speed = 5  # Reduce the speed below the base speed.

        ball.update()

        self.assertEqual(ball.speed, 5.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_add_collidable_sprite(self, mock_pygame, mock_load_png):
        mock_load_png.return_value = Mock(), Mock()
        mock_sprite, mock_bounce, mock_on_collide = Mock(), Mock(), Mock()

        ball = Ball((100, 100), 2.36, 8)

        ball.add_collidable_sprite(mock_sprite,
                                   bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)

        ball._collidable_sprites.add.assert_called_once_with(mock_sprite)
        self.assertEqual(len(ball._collision_data), 1)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_remove_collidable_sprite(self, mock_pygame, mock_load_png):
        mock_load_png.return_value = Mock(), Mock()
        mock_sprite1, mock_sprite2, mock_bounce, mock_on_collide = (
            Mock(), Mock(), Mock(), Mock())

        ball = Ball((100, 100), 2.36, 8)

        ball.add_collidable_sprite(mock_sprite1, bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)

        ball.add_collidable_sprite(mock_sprite2, bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)
        ball.remove_collidable_sprite(mock_sprite1)

        ball._collidable_sprites.remove.assert_called_once_with(mock_sprite1)
        self.assertEqual(len(ball._collision_data), 1)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_remove_collidable_sprite_no_exist(self, mock_pygame,
                                               mock_load_png):
        mock_load_png.return_value = Mock(), Mock()
        mock_sprite1, mock_sprite2, mock_bounce, mock_on_collide = (
            Mock(), Mock(), Mock(), Mock())

        ball = Ball((100, 100), 2.36, 8)

        ball.add_collidable_sprite(mock_sprite2, bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)
        ball.remove_collidable_sprite(mock_sprite1)  # Does not exist.

        ball._collidable_sprites.remove.assert_called_once_with(mock_sprite1)
        self.assertEqual(len(ball._collision_data), 1)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_remove_all_collidable_sprite(self, mock_pygame, mock_load_png):
        mock_load_png.return_value = Mock(), Mock()
        mock_sprite1, mock_sprite2, mock_bounce, mock_on_collide = (
            Mock(), Mock(), Mock(), Mock())

        ball = Ball((100, 100), 2.36, 8)

        ball.add_collidable_sprite(mock_sprite1, bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)

        ball.add_collidable_sprite(mock_sprite2, bounce_strategy=mock_bounce,
                                   speed_adjust=0.05,
                                   on_collide=mock_on_collide)
        ball.remove_all_collidable_sprites()

        ball._collidable_sprites.empty.assert_called_once_with()
        self.assertEqual(len(ball._collision_data), 0)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_single_sprite_collision(self, mock_pygame, mock_load_png):
        """Test that a bounce strategy is used, the ball speed adjusted, and
        a collision callback invoked when the ball collides with a single
        sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_bounce, mock_on_collide = Mock(), Mock()

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        mock_bounce.return_value = 2.4

        ball = Ball((100, 100), 2.36, 8)
        ball.add_collidable_sprite(mock_sprite, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball.update()

        self.assertEqual(ball.speed, 8.5)
        mock_on_collide.assert_called_once_with(mock_sprite, ball)
        mock_bounce.assert_called_once_with(mock_sprite.rect, ball.rect)
        self.assertEqual(ball.angle, 2.4)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_single_sprite_collision_default(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation is used, the ball speed
        adjusted, and a collision callback invoked when the ball collides with
        a single sprites which does not have an associated ball bounce
        strategy callback.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_on_collide, mock_calc_new_angle = Mock(), Mock()

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        ball = Ball((100, 100), 2.36, 8)
        ball.add_collidable_sprite(mock_sprite, speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball._calc_new_angle = mock_calc_new_angle
        ball.update()

        self.assertEqual(ball.speed, 8.5)
        mock_on_collide.assert_called_once_with(mock_sprite, ball)
        mock_calc_new_angle.assert_called_once_with([mock_sprite.rect])

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_multiple_sprite_collision(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation is used, the ball speed
        adjusted, and collision callbacks invoked when the ball collides with
        multiple sprites.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        (mock_bounce,
         mock_on_collide,
         mock_calc_new_angle,
         mock_sprite2,
         mock_sprite3) = (Mock(), Mock(), Mock(), Mock(), Mock())

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite,
                                                         mock_sprite2,
                                                         mock_sprite3]

        mock_bounce.return_value = 3.2

        ball = Ball((100, 100), 2.36, 8, top_speed=9)
        ball.add_collidable_sprite(mock_sprite, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball.add_collidable_sprite(mock_sprite2, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball.add_collidable_sprite(mock_sprite3, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball._calc_new_angle = mock_calc_new_angle
        ball.update()

        self.assertEqual(ball.speed, 9.0)  # Gone up, but not above top speed.
        mock_on_collide.assert_has_calls([call(mock_sprite, ball),
                                          call(mock_sprite2, ball),
                                          call(mock_sprite3, ball)])
        mock_calc_new_angle.assert_called_once_with([mock_sprite.rect,
                                                     mock_sprite2.rect,
                                                     mock_sprite3.rect])

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_single_corner(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (95.0, 95.0)

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 3.92, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 0.78 - RANDOM_RANGE)
        self.assertLess(ball.angle, 0.78 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_top_left_h(self, mock_pygame,
                                                      mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is horizontally oblique against the top
        left corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (104.0, 94.0)  # Top left corner

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100),  5.3, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 0.98 - RANDOM_RANGE)
        self.assertLess(ball.angle, 0.98 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_top_right_h(self, mock_pygame,
                                                       mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is horizontally oblique against the top
        right corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (115.0, 105.0)  # Top right corner.

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100),  0.78, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 2.36 - RANDOM_RANGE)
        self.assertLess(ball.angle, 2.36 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_top_left_v(self, mock_pygame,
                                                      mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is vertically oblique against the top
        left corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (95.0, 105.0)  # Top left corner.

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100),  2.35, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 0.78 - RANDOM_RANGE)
        self.assertLess(ball.angle, 0.78 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_top_right_v(self, mock_pygame,
                                                       mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is vertically oblique against the top
        right corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (115.0, 105.0)  # Top right corner.

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100),  0.78, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 2.36 - RANDOM_RANGE)
        self.assertLess(ball.angle, 2.36 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_bottom_left_h(self, mock_pygame,
                                                         mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is horizontally oblique against the bottom
        left corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (105.0, 115.0)  # Bottom left corner

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 0.78, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 5.5 - RANDOM_RANGE)
        self.assertLess(ball.angle, 5.5 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_bottom_right_h(self, mock_pygame,
                                                          mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is horizontally oblique against the bottom
        right corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (105.0, 115.0)  # Bottom right corner

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 2.36, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 3.92 - RANDOM_RANGE)
        self.assertLess(ball.angle, 3.92 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_bottom_left_v(self, mock_pygame,
                                                         mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is vertically oblique against the bottom
        left corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (95.0, 105.0)  # Bottom left corner

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 3.92, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 5.5 - RANDOM_RANGE)
        self.assertLess(ball.angle, 5.5 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_corner_oblique_bottom_right_v(self, mock_pygame,
                                                          mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite
        but the angle of collision is vertically oblique against the bottom
        right corner of the ball, rather than head on.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            return point == (115.0, 105.0)  # Bottom left corner

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 5.5, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 3.92 - RANDOM_RANGE)
        self.assertLess(ball.angle, 3.92 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_three_corners(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with three corners of a sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 94.0), (105.0, 94.0), (95.0, 104.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.01, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertAlmostEqual(ball.angle, 0.87, places=2)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_all_corners(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with all corners of a sprite (is
        effectively inside the sprite).
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        mock_sprite.rect.collidepoint.return_value = True

        ball = Ball((100, 100), 4.01, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertAlmostEqual(ball.angle, 0.87, places=2)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_top_collision(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the top of the ball collides with another sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 94.0), (105.0, 94.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.01, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 2.27 - RANDOM_RANGE)
        self.assertLess(ball.angle, 2.27 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_bottom_collision(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the bottom of the ball collides with another sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 115.0), (105.0, 115.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 2.32, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 3.96 - RANDOM_RANGE)
        self.assertLess(ball.angle, 3.96 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_top_invalid(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation does not calculate a new
        angle when the top of the ball collides but the angle is invalid for
        a top collision.

        Angles are calculated clockwise from the righthand x-axis, so in order
        for a top collision to occur, the ball must be travelling at an angle
        greater than 3.14. An angle less than this would be an invalid state.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 105.0), (105.0, 105.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 2.32, 8)  # Angle is incorrect for top collide
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        # Due to the invalid state, the ball's angle is not recalculated.
        self.assertGreaterEqual(ball.angle, 2.32 - RANDOM_RANGE)
        self.assertLess(ball.angle, 2.32 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_left_collision_1(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the left of the ball collides with another sprite and
        the current angle is less than PI.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 105.0), (95.0, 115.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 2.32, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 0.82 - RANDOM_RANGE)
        self.assertLess(ball.angle, 0.82 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_left_collision_2(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the left of the ball collides with another sprite and
        the current angle is greater than PI.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(95.0, 94.0), (95.0, 104.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.01, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 5.41 - RANDOM_RANGE)
        self.assertLess(ball.angle, 5.41 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_left_invalid(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation does not calculate a new
        angle when the left of the ball collides but the angle is invalid for
        a left collision.

        Angles are calculated clockwise from the righthand x-axis, so in order
        for a left collision to occur, the ball must be travelling at an angle
        greater than 1.57 and less than 4.71.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(101.0, 93.0), (101.0, 103.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.9, 8)  # Invalid angle for left collision.
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        # Due to the invalid state, the ball's angle is not recalculated.
        self.assertGreaterEqual(ball.angle, 4.9 - RANDOM_RANGE)
        self.assertLess(ball.angle, 4.9 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_right_collision_1(self, mock_pygame,
                                              mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the right of the ball collides with another sprite and
        the current angle is less than PI.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(112.0, 107.0), (112.0, 117.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 1.2, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 1.94 - RANDOM_RANGE)
        self.assertLess(ball.angle, 1.94 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_right_collision_2(self, mock_pygame,
                                              mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the right of the ball collides with another sprite and
        the current angle is greater than PI.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(111.0, 93.0), (111.0, 103.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.9, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 4.5 - RANDOM_RANGE)
        self.assertLess(ball.angle, 4.5 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_right_invalid(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation does not calculate a new
        angle when the right of the ball collides but the angle is invalid for
        a right collision.

        Angles are calculated clockwise from the righthand x-axis, so in order
        for a right collision to occur, the ball must be travelling at an angle
        greater than 4.71 or less than 1.57.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(111.0, 93.0), (111.0, 103.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 2.32, 8)  # Invalid angle for right collision.
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        # Due to the invalid state, the ball's angle is not recalculated.
        self.assertGreaterEqual(ball.angle, 2.32 - RANDOM_RANGE)
        self.assertLess(ball.angle, 2.32 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_top_collision_vertical(self, mock_pygame,
                                                   mock_load_png):
        """Test that the when the top of the ball bounces at a near
        vertical angle, that the angle of bounce is adjusted to more that
        what it would naturally be. This is to overcome bounce loops.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(100.0, 93.0), (110.0, 93.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 4.71, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 1.92 - RANDOM_RANGE)
        self.assertLess(ball.angle, 1.92 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_bottom_collision_vertical(self, mock_pygame,
                                                      mock_load_png):
        """Test that the when the bottom of the ball bounces at a near
        vertical angle, that the angle of bounce is adjusted to more that
        what it would naturally be. This is to overcome bounce loops.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(100.0, 117.0), (110.0, 117.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 1.57, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 5.06 - RANDOM_RANGE)
        self.assertLess(ball.angle, 5.06 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_left_collision_horizontal(self, mock_pygame,
                                                      mock_load_png):
        """Test that the when the left of the ball bounces at a near
        horizontal angle, that the angle of bounce is adjusted to more that
        what it would naturally be. This is to overcome bounce loops.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(93.0, 100.0), (93.0, 110.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 3.18, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 5.89 - RANDOM_RANGE)
        self.assertLess(ball.angle, 5.89 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calc_new_angle_right_collision_horizontal(self, mock_pygame,
                                                       mock_load_png):
        """Test that the when the right of the ball bounces at a near
        horizontal angle, that the angle of bounce is adjusted to more that
        what it would naturally be. This is to overcome bounce loops.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        def collidepoint(point):
            points = [(117.0, 100.0), (117.0, 110.0)]
            return point in points

        mock_sprite.rect.collidepoint.side_effect = collidepoint

        ball = Ball((100, 100), 6.25, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        self.assertGreaterEqual(ball.angle, 3.52 - RANDOM_RANGE)
        self.assertLess(ball.angle, 3.52 + RANDOM_RANGE + 0.03)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_clone_ball(self, mock_pygame, mock_load_png):
        self._configure_mocks(mock_pygame, mock_load_png)

        ball = Ball((100, 100), 2.32, 8)

        sprite, bounce, on_collide, offscreen = Mock(), Mock(), Mock(), Mock()
        ball._collidable_sprites.__iter__.return_value = [sprite]

        ball.add_collidable_sprite(sprite,
                                   bounce_strategy=bounce,
                                   speed_adjust=2,
                                   on_collide=on_collide)

        clone = ball.clone(start_pos=(200, 200),
                           start_angle=3.01,
                           base_speed=9,
                           top_speed=14,
                           normalisation_rate=0.3,
                           off_screen_callback=offscreen)

        self.assertEqual(clone._start_pos, (200, 200))
        self.assertEqual(clone._start_angle, 3.01)
        self.assertEqual(clone.base_speed, 9)
        self.assertEqual(clone._top_speed, 14)
        self.assertEqual(clone.normalisation_rate, 0.3)
        self.assertEqual(clone._off_screen_callback, offscreen)
        clone._collidable_sprites.add.assert_has_calls([call(sprite)])
        self.assertEqual(clone._collision_data, ball._collision_data)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_anchor_static_object(self, mock_pygame, mock_load_png):
        """Test that the ball's position is not recalculated when the ball is
        anchored to a static object.
        """
        self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.32, 8)
        ball.anchor((200, 200))
        ball.update()

        # Assert that a new Rectangle mock was called with the fixed
        # position and dimensions of the anchored ball.
        mock_pygame.Rect.assert_called_once_with((200, 200), (10, 10))

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_anchor_sprite(self, mock_pygame, mock_load_png):
        """Test that the ball's position is not recalculated when the ball is
        anchored relative to another sprite.
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_sprite.rect.left = 305
        mock_sprite.rect.top = 429

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.32, 8)
        ball.anchor(mock_sprite, rel_pos=(5, 5))
        ball.update()

        # Assert that a new Rectangle mock was called with the position
        # of the sprite taking into account the relative position.
        mock_pygame.Rect.assert_called_once_with(305 + 5, 429 + 5, 10, 10)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_no_collision_when_ball_anchored(self, mock_pygame, mock_load_png):
        """Test that the ball's collision detection behaviour does not
        execute when the ball is anchored (not free moving itself).
        """
        mock_sprite = self._configure_mocks(mock_pygame, mock_load_png)
        mock_sprite.rect.left = 305
        mock_sprite.rect.top = 429

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.32, 8)
        ball.anchor(mock_sprite, rel_pos=(5, 5))
        ball.update()

        self.assertEqual(mock_pygame.sprite.spritecollide.call_count, 0)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_release_anchor(self, mock_pygame, mock_load_png):
        """Test that an anchored ball is released."""
        self._configure_mocks(mock_pygame, mock_load_png)

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.32, 8)
        ball.anchor((200, 200))
        ball.update()
        ball.release(4.01)

        self.assertIsNone(ball._anchor)
        self.assertEqual(ball.angle, 4.01)
