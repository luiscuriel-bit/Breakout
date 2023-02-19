import random
from typing import TypeVar

from gale.factory import Factory

import settings
from src.Cannon_Projectiles import Cannon_Projectiles
from src.powerups.PowerUp import PowerUp


class Cannons(PowerUp):

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 1)
        self.projectiles_factory = Factory(Cannon_Projectiles)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        if not len(play_state.projectiles):
            projectile1 = self.projectiles_factory.create(play_state.paddle.x, play_state.paddle.y)
            projectile2 = self.projectiles_factory.create(play_state.paddle.x + play_state.paddle.width,    play_state.paddle.y)

            settings.SOUNDS["paddle_hit"].stop()
            settings.SOUNDS["paddle_hit"].play()
            play_state.projectiles.append(projectile1)
            play_state.projectiles.append(projectile2)

        self.in_play = False
