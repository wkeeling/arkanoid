from unittest.case import TestCase
from unittest.mock import (call,
                           Mock,
                           patch)

import pygame

from arkanoid.sprites.ball import Ball


class TestBall(TestCase):

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_calculate_new_position(self, mock_pygame, mock_load_png):
        mock_image, mock_screen, mock_area = Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

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
        mock_image, mock_screen, mock_area = Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = False

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
        mock_image, mock_screen, mock_area = Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

        mock_pygame.sprite.spritecollide.return_value = []

        ball = Ball((100, 100), 2.36, 8, normalisation_rate=0.03)
        ball.speed = 12  # Increase the speed above the base speed.

        ball.update()

        self.assertEqual(ball.speed, 11.97)

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_speed_normalised_up_when_no_collision(self, mock_pygame,
                                                   mock_load_png):
        mock_image, mock_screen, mock_area = Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

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

        ball.add_collidable_sprite(mock_sprite, bounce_strategy=mock_bounce,
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
        (mock_image,
         mock_screen,
         mock_area,
         mock_sprite,
         mock_bounce,
         mock_on_collide) = Mock(), Mock(), Mock(), Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

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
        (mock_image,
         mock_screen,
         mock_area,
         mock_sprite,
         mock_on_collide,
         mock_calc_new_angle) = Mock(), Mock(), Mock(), Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

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
        (mock_image,
         mock_screen,
         mock_area,
         mock_sprite1,
         mock_sprite2,
         mock_bounce,
         mock_on_collide,
         mock_calc_new_angle) = (
            Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock())

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite1,
                                                         mock_sprite2]

        mock_bounce.return_value = 3.2

        ball = Ball((100, 100), 2.36, 8)
        ball.add_collidable_sprite(mock_sprite1, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball.add_collidable_sprite(mock_sprite2, bounce_strategy=mock_bounce,
                                   speed_adjust=0.5,
                                   on_collide=mock_on_collide)
        ball._calc_new_angle = mock_calc_new_angle
        ball.update()

        self.assertEqual(ball.speed, 9.0)
        mock_on_collide.assert_has_calls([call(mock_sprite1, ball),
                                          call(mock_sprite2, ball)])
        mock_calc_new_angle.assert_called_once_with([mock_sprite1.rect,
                                                     mock_sprite2.rect])

    @patch('arkanoid.sprites.ball.load_png')
    @patch('arkanoid.sprites.ball.pygame')
    def test_cal_new_angle_single_corner(self, mock_pygame, mock_load_png):
        """Test that the default bounce calculation correctly calculates
        the angle when the ball collides with a single corner of a sprite.
        """
        (mock_image,
         mock_screen,
         mock_area,
         mock_sprite) = Mock(), Mock(), Mock(), Mock()

        # Use a real pygame.Rect for the rect value.
        mock_load_png.return_value = mock_image, pygame.Rect(0, 0, 10, 10)
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_screen.get_rect.return_value = mock_area
        mock_area.contains.return_value = True

        mock_pygame.sprite.spritecollide.return_value = [mock_sprite]

        ball = Ball((100, 100), 2.36, 8)
        ball.add_collidable_sprite(mock_sprite)
        ball.update()

        # TODO: get this working, plus the other angle tests
        self.assertEqual(ball.angle, 8888)
