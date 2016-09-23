import math
from unittest import TestCase
from unittest.mock import (ANY,
                           call,
                           Mock,
                           patch)

import pygame

from arkanoid.sprites.paddle import (LaserBullet,
                                     LaserState,
                                     Paddle)


class TestPaddle(TestCase):

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_initialise(self, mock_pygame, mock_load_png,
                        mock_load_png_sequence):
        mock_screen, mock_area, mock_image, mock_rect = (
            Mock(), Mock(), Mock(), Mock())
        mock_screen.left = 0
        mock_screen.height = 650
        mock_screen.width = 600
        mock_rect.height = 10
        mock_pygame.Rect.return_value = mock_area
        mock_area.center = 'area center'
        mock_pygame.display.get_surface.return_value.get_rect.return_value = \
            mock_screen
        mock_load_png.return_value = mock_image, mock_rect

        paddle = Paddle(left_offset=10, right_offset=10, bottom_offset=20)

        self.assertEqual(paddle.image, mock_image)
        self.assertEqual(paddle.rect, mock_rect)
        self.assertIs(paddle.visible, True)
        mock_pygame.Rect.assert_called_once_with(10, 630, 580, 10)
        self.assertEqual(paddle.rect.center, 'area center')

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_update_moves_when_in_area(self, mock_pygame, mock_load_png,
                                       mock_load_png_sequence):
        mock_image, mock_rect, mock_area, mock_new_rect = (
            Mock(), Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_pygame.Rect.return_value = mock_area
        mock_rect.move.return_value = mock_new_rect
        mock_area.contains.return_value = True

        paddle = Paddle()
        paddle.move_left()
        paddle.update()

        self.assertEqual(paddle.rect, mock_new_rect)

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_update_not_move_when_not_in_area(self, mock_pygame,
                                              mock_load_png,
                                              mock_load_png_sequence):
        mock_image, mock_rect, mock_new_rect, mock_area_contains = (
            Mock(), Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_rect.move.return_value = mock_new_rect
        mock_area_contains.return_value = False

        paddle = Paddle()
        paddle._area_contains = mock_area_contains
        paddle.move_left()
        paddle.update()

        self.assertEqual(paddle.rect, mock_rect)

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_move_left(self, mock_pygame, mock_load_png,
                       mock_load_png_sequence):
        mock_image, mock_rect, mock_area = (Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_pygame.Rect.return_value = mock_area
        mock_area.contains.return_value = True

        paddle = Paddle()
        paddle.move_left()
        paddle.update()

        mock_rect.move.assert_called_once_with(-10, 0)

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_move_right(self, mock_pygame, mock_load_png,
                        mock_load_png_sequence):
        mock_image, mock_rect, mock_area = (Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_pygame.Rect.return_value = mock_area
        mock_area.contains.return_value = True

        paddle = Paddle(speed=15)
        paddle.move_right()
        paddle.update()

        mock_rect.move.assert_called_once_with(15, 0)

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_stop(self, mock_pygame, mock_load_png,
                  mock_load_png_sequence):
        mock_image, mock_rect, mock_area = (Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_pygame.Rect.return_value = mock_area
        mock_area.contains.return_value = True

        paddle = Paddle()
        paddle.stop()
        # Should not attempt to move the paddle now it is stopped.
        paddle.update()

        self.assertEqual(mock_rect.move.call_count, 0)

    @patch('arkanoid.sprites.paddle.load_png_sequence')
    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_reset(self, mock_pygame, mock_load_png,
                   mock_load_png_sequence):
        mock_image, mock_rect, mock_area = (Mock(), Mock(), Mock())
        mock_load_png.return_value = mock_image, mock_rect
        mock_pygame.Rect.return_value = mock_area
        mock_area.contains.return_value = True
        mock_area.center = 'the centre'

        paddle = Paddle()
        paddle.reset()
        paddle.update()

        self.assertEqual(mock_rect.center, 'the centre')

    def test_bounce_strategy(self):
        angles = []
        paddle = pygame.Rect(100, 600, 60, 15)

        for i in range(103, 163, 10):
            ball = pygame.Rect(i, 602, 5, 5)
            angle = Paddle.bounce_strategy(paddle, ball)
            angles.append(int(math.degrees(angle)))

        self.assertEqual(angles[0], 220)
        self.assertEqual(angles[1], 245)
        self.assertEqual(angles[2], 260)
        self.assertEqual(angles[3], 280)
        self.assertEqual(angles[4], 295)
        self.assertEqual(angles[5], 320)


class TestLaserState(TestCase):

    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.receiver')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_convert_to_laser(self, mock_load_png_sequence, mock_receiver,
                              mock_pulsator):
        img1, rect1, img2, rect2, img3, rect3 = (
            Mock(), Mock(), Mock(), Mock(), Mock(), Mock())
        mock_image_sequence = [(img1, rect1), (img2, rect2), (img3, rect3)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)

        state = LaserState(mock_paddle, None)

        state.update()

        self.assertEqual(state.paddle.image, img1)
        self.assertEqual(state.paddle.rect, rect1)
        self.assertEqual(rect1.center, (100, 100))

        state.update()

        self.assertEqual(state.paddle.image, img2)
        self.assertEqual(state.paddle.rect, rect2)
        self.assertEqual(rect2.center, (100, 100))

        state.update()

        self.assertEqual(state.paddle.image, img3)
        self.assertEqual(state.paddle.rect, rect3)
        self.assertEqual(rect3.center, (100, 100))

        state.update()
        state.update()

        self.assertEqual(state._to_laser, False)
        mock_receiver.register_handler.assert_called_once_with(pygame.KEYUP,
                                                               state._fire)
        mock_pulsator.assert_called_once_with(mock_paddle,
                                              'paddle_laser_pulsate')
        mock_pulsator.return_value.update.assert_called_once_with()

    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.receiver')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_convert_from_laser(self, mock_load_png_sequence, mock_receiver,
                                mock_pulsator):
        img1, rect1, img2, rect2, img3, rect3 = (
            Mock(), Mock(), Mock(), Mock(), Mock(), Mock())
        mock_image_sequence = [(img1, rect1), (img2, rect2), (img3, rect3)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_on_exit = Mock()

        state = LaserState(mock_paddle, None)
        state.exit(on_exit=mock_on_exit)

        state.update()

        self.assertEqual(state.paddle.image, img3)
        self.assertEqual(state.paddle.rect, rect3)
        self.assertEqual(rect3.center, (100, 100))

        state.update()

        self.assertEqual(state.paddle.image, img2)
        self.assertEqual(state.paddle.rect, rect2)
        self.assertEqual(rect2.center, (100, 100))

        state.update()

        self.assertEqual(state.paddle.image, img1)
        self.assertEqual(state.paddle.rect, rect1)
        self.assertEqual(rect1.center, (100, 100))

        state.update()

        self.assertEqual(state._from_laser, False)
        mock_receiver.unregister_handler.assert_called_once_with(state._fire)
        mock_on_exit.assert_called_once_with()

    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_nudge_right_on_convert(self, mock_load_png_sequence,
                                    mock_pulsator):
        img, rect = Mock(), Mock()
        rect.move.return_value = rect
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.area.collidepoint.side_effect = False, False, True

        state = LaserState(mock_paddle, None)
        state.update()

        mock_paddle.rect.move.assert_has_calls([call(1, 0), call(1, 0)])

    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_nudge_left_on_convert(self, mock_load_png_sequence,
                                   mock_pulsator):
        img, rect = Mock(), Mock()
        rect.move.return_value = rect
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.area.collidepoint.side_effect = True, False, False, True

        state = LaserState(mock_paddle, None)
        state.update()

        mock_paddle.rect.move.assert_has_calls([call(-1, 0), call(-1, 0)])

    @patch('arkanoid.sprites.paddle.LaserBullet')
    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_fire(self, mock_load_png_sequence, mock_pulsator,
                  mock_bullet_class):
        img, rect = Mock(), Mock()
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.rect.bottomleft = (60, 120)
        mock_paddle.rect.width = 50
        mock_game = Mock()
        mock_event = Mock()
        mock_event.key = pygame.K_SPACE
        mock_bullet1, mock_bullet2 = Mock(), Mock()
        mock_bullet_class.side_effect = mock_bullet1, mock_bullet2

        state = LaserState(mock_paddle, mock_game)
        state._fire(mock_event)

        mock_bullet_class.assert_has_calls(
            [call(mock_game, position=(70, 120)),
             call(mock_game, position=(100, 120))])
        self.assertEqual(len(state._bullets), 2)
        mock_game.sprites.append.assert_has_calls([call(mock_bullet1),
                                                   call(mock_bullet2)])
        mock_bullet1.release.assert_called_once_with()
        mock_bullet2.release.assert_called_once_with()

    @patch('arkanoid.sprites.paddle.LaserBullet')
    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_fire_second_pair(self, mock_load_png_sequence, mock_pulsator,
                              mock_bullet_class):
        """Test it is possible to fire 2 more bullets if there are already
        2 in the air.
        """
        img, rect = Mock(), Mock()
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.rect.bottomleft = (60, 120)
        mock_paddle.rect.width = 50
        mock_game = Mock()
        mock_event = Mock()
        mock_event.key = pygame.K_SPACE

        state = LaserState(mock_paddle, mock_game)
        state._bullets.extend([Mock(), Mock()])
        state._fire(mock_event)

        self.assertEqual(mock_bullet_class.call_count, 2)

    @patch('arkanoid.sprites.paddle.LaserBullet')
    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_fire_max(self, mock_load_png_sequence, mock_pulsator,
                      mock_bullet_class):
        """Test that it is not possible to fire 2 more bullets if there are
        already 3 or more in the air.
        """
        img, rect = Mock(), Mock()
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.rect.bottomleft = (60, 120)
        mock_paddle.rect.width = 50
        mock_game = Mock()
        mock_event = Mock()
        mock_event.key = pygame.K_SPACE

        state = LaserState(mock_paddle, mock_game)
        state._bullets.extend([Mock()] * 3)
        state._fire(mock_event)

        self.assertEqual(mock_bullet_class.call_count, 0)

    @patch('arkanoid.sprites.paddle.LaserBullet')
    @patch('arkanoid.sprites.paddle._PaddlePulsator')
    @patch('arkanoid.sprites.paddle.load_png_sequence')
    def test_fire_no_space(self, mock_load_png_sequence, mock_pulsator,
                           mock_bullet_class):
        """Test that fire does not happen when spacebar not pressed.
        """
        img, rect = Mock(), Mock()
        mock_image_sequence = [(img, rect)]
        mock_load_png_sequence.return_value = mock_image_sequence
        mock_paddle = Mock()
        mock_paddle.rect.center = (100, 100)
        mock_paddle.rect.bottomleft = (60, 120)
        mock_paddle.rect.width = 50
        mock_game = Mock()
        mock_event = Mock()
        mock_event.key = pygame.KEYUP

        state = LaserState(mock_paddle, mock_game)
        state._fire(mock_event)

        self.assertEqual(mock_bullet_class.call_count, 0)


class TestLaserBullet(TestCase):

    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_initialise(self, mock_pygame, mock_load_png):
        mock_load_png.return_value = Mock(), Mock()
        bullet = LaserBullet(Mock(), Mock())

        mock_load_png.assert_called_once_with('laser_bullet')
        mock_pygame.display.get_surface.assert_called_once_with()
        mock_pygame.display.get_surface.return_value.\
            get_rect.assert_called_once_with()
        self.assertFalse(bullet.visible)

    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_release(self, mock_pygame, mock_load_png):
        mock_rect = Mock()
        mock_load_png.return_value = Mock(), mock_rect
        bullet = LaserBullet(Mock(), (20, 20))

        bullet.release()

        self.assertEqual(mock_rect.midbottom, (20, 20))
        self.assertTrue(bullet.visible)

    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_collide_brick(self, mock_pygame, mock_load_png):
        mock_game, mock_rect = Mock(), Mock()
        mock_load_png.return_value = Mock(), mock_rect
        bullet = LaserBullet(mock_game, Mock())
        bullet.release()
        mock_rect.move.return_value = mock_rect
        visible_bricks = [Mock()]
        mock_game.round.bricks = visible_bricks
        mock_pygame.sprite.spritecollide.side_effect = [[], visible_bricks]

        bullet.update()

        mock_rect.move.assert_called_once_with(0, -15)
        mock_pygame.sprite.spritecollide. \
            assert_has_calls([call(bullet, [mock_game.round.edges.top], False),
                              call(bullet, ANY, False)])
        mock_brick = visible_bricks[0]
        self.assertEqual(mock_brick.value, 0)
        self.assertIsNone(mock_brick.powerup_cls)
        mock_game.on_brick_collide.assert_called_once_with(mock_brick, bullet)
        self.assertFalse(bullet.visible)

    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_collide_enemy(self, mock_pygame, mock_load_png):
        mock_game, mock_rect = Mock(), Mock()
        mock_load_png.return_value = Mock(), mock_rect
        bullet = LaserBullet(mock_game, Mock())
        bullet.release()
        mock_rect.move.return_value = mock_rect
        visible_bricks = []
        mock_game.round.bricks = visible_bricks
        visible_enemies = [Mock()]
        mock_game.enemies = visible_enemies
        mock_pygame.sprite.spritecollide.side_effect = [[], visible_bricks,
                                                        visible_enemies]

        bullet.update()

        mock_rect.move.assert_called_once_with(0, -15)
        mock_pygame.sprite.spritecollide. \
            assert_has_calls([call(bullet, [mock_game.round.edges.top], False),
                              call(bullet, ANY, False),
                              call(bullet, ANY, False)])
        self.assertEqual(mock_game.on_brick_collide.call_count, 0)
        mock_enemy = visible_enemies[0]
        mock_game.on_enemy_collide.assert_called_once_with(mock_enemy, bullet)
        self.assertFalse(bullet.visible)

    @patch('arkanoid.sprites.paddle.load_png')
    @patch('arkanoid.sprites.paddle.pygame')
    def test_collide_edge(self, mock_pygame, mock_load_png):
        mock_game, mock_rect = Mock(), Mock()
        mock_load_png.return_value = Mock(), mock_rect
        bullet = LaserBullet(mock_game, Mock())
        bullet.release()
        mock_rect.move.return_value = mock_rect
        mock_game.round.edges.top.rect.colliderect.return_value = True

        bullet.update()

        self.assertFalse(bullet.visible)
