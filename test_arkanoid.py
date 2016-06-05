import math
from unittest import TestCase

import pygame

import arkanoid


class TestPaddle(TestCase):

    def test_bounce_strategy(self):
        angles = []
        paddle = pygame.Rect(100, 600, 80, 15)

        for i in range(103, 183, 10):
            ball = pygame.Rect(i, 602, 5, 5)
            angle = arkanoid.Paddle.bounce_strategy(paddle, ball)
            angles.append(math.floor(math.degrees(angle)))

        self.assertEqual(angles, [-150, -130, -115, -100, -80, -65, -50, -30])
