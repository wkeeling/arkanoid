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
            angles.append(int(math.degrees(angle)))

        self.assertTrue(-140 <= angles[0] <= -135, angles[0])
        self.assertTrue(-125 <= angles[1] <= -115, angles[1])
        self.assertTrue(-115 <= angles[2] <= -105, angles[2])
        self.assertTrue(-105 <= angles[3] <= -95, angles[3])
        self.assertTrue(-85 <= angles[4] <= -75, angles[4])
        self.assertTrue(-75 <= angles[5] <= -65, angles[5])
        self.assertTrue(-65 <= angles[6] <= -55, angles[6])
        self.assertTrue(-50 <= angles[7] <= -40, angles[7])

