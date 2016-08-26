from unittest import TestCase
from unittest.mock import (Mock,
                           patch)

from arkanoid.sprites.brick import (Brick,
                                    BrickColour)


class TestBrick(TestCase):

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_loads_image_on_initiaise(self, mock_load_png,
                                      mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        Brick(BrickColour.red, 1, powerup_cls=Mock())

        mock_load_png.assert_called_once_with('brick_red')

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_loads_image_sequence_on_initiaise(self, mock_load_png,
                                               mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()
        mock_load_png_sequence.return_value = ((Mock(), Mock()), )

        Brick(BrickColour.red, 1, powerup_cls=Mock())

        mock_load_png_sequence.assert_called_once_with('brick_red')

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_initiaise_score_value_non_silver(self, mock_load_png,
                                              mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        red_brick = Brick(BrickColour.red, 1, powerup_cls=Mock())

        self.assertEqual(red_brick.value, 90)

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_initiaise_score_value_silver(self, mock_load_png,
                                          mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        silver_brick = Brick(BrickColour.silver, 3, powerup_cls=Mock())

        self.assertEqual(silver_brick.value, 150)

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_initiaise_sets_powerup_class(self, mock_load_png,
                                          mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()
        powerup_class = Mock()

        red_brick = Brick(BrickColour.red, 1, powerup_cls=powerup_class)

        self.assertEqual(red_brick.powerup_cls, powerup_class)

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_visible_red(self, mock_load_png, mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        red_brick = Brick(BrickColour.red, 1, powerup_cls=Mock())

        self.assertTrue(red_brick.visible)
        red_brick.collision_count += 1
        self.assertFalse(red_brick.visible)

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_visible_silver(self, mock_load_png, mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        silver_brick = Brick(BrickColour.silver, 1, powerup_cls=Mock())

        self.assertTrue(silver_brick.visible)
        silver_brick.collision_count += 1
        self.assertTrue(silver_brick.visible)
        silver_brick.collision_count += 1
        self.assertFalse(silver_brick.visible)

    @patch('arkanoid.sprites.brick.load_png_sequence')
    @patch('arkanoid.sprites.brick.load_png')
    def test_visible_gold(self, mock_load_png, mock_load_png_sequence):

        mock_load_png.return_value = Mock(), Mock()

        gold_brick = Brick(BrickColour.gold, 1, powerup_cls=Mock())

        self.assertTrue(gold_brick.visible)
        gold_brick.collision_count += 100
        self.assertTrue(gold_brick.visible)

