from unittest import TestCase
from unittest.mock import (call,
                           Mock,
                           patch)

from arkanoid.rounds.base import BaseRound
from arkanoid.sprites.brick import BrickColour


class TestBaseRound(TestCase):

    @patch('arkanoid.rounds.base.pygame')
    def test_sets_brick_in_position_0_0(self, mock_pygame):
        mock_screen, mock_background, mock_brick = self._setup_mocks(
            mock_pygame)

        base_round = BaseRound(top_offset=150)
        base_round._blit_brick(mock_brick, x=0, y=0)

        mock_screen.blit.assert_has_calls([call(mock_background, (0, 150)),
                                           call(mock_brick.image, (15, 165))])

    @patch('arkanoid.rounds.base.pygame')
    def test_sets_brick_in_position_1_1(self, mock_pygame):
        mock_screen, mock_background, mock_brick = self._setup_mocks(
            mock_pygame)

        base_round = BaseRound(top_offset=150)
        base_round._blit_brick(mock_brick, x=1, y=1)

        mock_screen.blit.assert_has_calls([call(mock_background, (0, 150)),
                                           call(mock_brick.image, (57, 186))])

    @patch('arkanoid.rounds.base.pygame')
    def test_sets_brick_in_position_9_13(self, mock_pygame):
        mock_screen, mock_background, mock_brick = self._setup_mocks(
            mock_pygame)

        base_round = BaseRound(top_offset=150)
        base_round._blit_brick(mock_brick, x=9, y=13)

        mock_screen.blit.assert_has_calls([call(mock_background, (0, 150)),
                                           call(mock_brick.image, (393, 438))])

    def _setup_mocks(self, mock_pygame):
        mock_screen = Mock()
        mock_pygame.display.get_surface.return_value = mock_screen
        mock_edges = Mock()
        mock_edges.left.rect.x = 0
        mock_edges.left.rect.width = 15
        mock_edges.top.rect.y = 150
        mock_edges.top.rect.height = 15
        mock_create_edges = Mock()
        mock_create_edges.return_value = mock_edges
        mock_background = Mock()
        mock_create_background = Mock()
        mock_create_background.return_value = mock_background
        mock_create_bricks = Mock()
        BaseRound._create_edges = mock_create_edges
        BaseRound._create_background = mock_create_background
        BaseRound._create_bricks = mock_create_bricks
        mock_image, mock_rect = Mock(), Mock()
        mock_brick = Mock()
        mock_brick.image = mock_image
        mock_brick.rect = mock_rect
        mock_brick.rect.width = 42
        mock_brick.rect.height = 21

        return mock_screen, mock_background, mock_brick

    @patch('arkanoid.rounds.base.pygame')
    def test_round_complete(self, mock_pygame):
        mock_create_edges = Mock()
        mock_create_background = Mock()
        mock_create_bricks = Mock()
        mock_create_bricks.return_value = [
            Mock(colour=BrickColour.blue) if i % 2 == 0 else
            Mock(colour=BrickColour.gold) for i in range(20)]
        BaseRound._create_edges = mock_create_edges
        BaseRound._create_background = mock_create_background
        BaseRound._create_bricks = mock_create_bricks

        base_round = BaseRound(None)

        for _ in range(11):
            base_round.brick_destroyed()

        self.assertTrue(base_round.complete)

    @patch('arkanoid.rounds.base.pygame')
    def test_round_incomplete(self, mock_pygame):
        mock_create_edges = Mock()
        mock_create_background = Mock()
        mock_create_bricks = Mock()
        mock_create_bricks.return_value = [
            Mock(colour=BrickColour.blue) if i % 2 == 0 else
            Mock(colour=BrickColour.gold) for i in range(20)]
        BaseRound._create_edges = mock_create_edges
        BaseRound._create_background = mock_create_background
        BaseRound._create_bricks = mock_create_bricks

        base_round = BaseRound(None)

        for _ in range(5):
            base_round.brick_destroyed()

        self.assertFalse(base_round.complete)
