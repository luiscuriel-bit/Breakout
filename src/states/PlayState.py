"""
ISPPJ1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class to define the Play state.
"""
import random

import pygame

from gale.factory import AbstractFactory
from gale.state_machine import BaseState
from gale.input_handler import InputHandler, InputData, InputData
from gale.text import render_text

import settings
import src.powerups


class PlayState(BaseState):
    def enter(self, **params: dict):
        self.level = params["level"]
        self.score = params["score"]
        self.lives = params["lives"]
        self.paddle = params["paddle"]
        self.balls = params["balls"]
        self.brickset = params["brickset"]
        self.live_factor = params["live_factor"]
        self.points_to_next_live = params["points_to_next_live"]
        self.points_to_next_grow_up = (
            self.score
            + settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
        )
        self.powerups = params.get("powerups", [])
        self.counter = params.get("counter", 0)        
        self.sticky = params.get("sticky", False)
        self.timer = params.get("timer", 10)
        self.projectiles = params.get("projectiles", [])
        self.multiplier2x = params.get("multiplier2x", False)
 

        if not params.get("resume", False):
            self.balls[0].vx = random.randint(-80, 80)
            self.balls[0].vy = random.randint(-170, -100)
            settings.SOUNDS["paddle_hit"].play()

        self.powerups_abstract_factory = AbstractFactory("src.powerups")

        InputHandler.register_listener(self)

    def exit(self) -> None:
        InputHandler.unregister_listener(self)

    def update(self, dt: float) -> None:
        self.paddle.update(dt)

        for ball in self.balls:
            ball.update(dt)
            ball.solve_world_boundaries()

            if ball.attached:
                ball.x = self.paddle.x + self.paddle.width / 2 - ball.width / 2
                ball.y = self.paddle.y - ball.height 

            # Check collision with the paddle
            if ball.collides(self.paddle):
                if self.sticky and (not ball.attached):
                    ball.attached = True
                    ball.vx = 0
                    ball.vy = 0
                else:
                    settings.SOUNDS["paddle_hit"].stop()
                    settings.SOUNDS["paddle_hit"].play()
                    ball.rebound(self.paddle)
                    ball.push(self.paddle)

            # Check collision with brickset
            if not ball.collides(self.brickset):
                continue

            brick = self.brickset.get_colliding_brick(ball.get_collision_rect())

            if brick is None:
                continue

            brick.hit()
            if self.multiplier2x:
                 self.score += 2 * brick.score()
            else:
                 self.score += brick.score()
            ball.rebound(brick)

            # Check earn life
            if self.score >= self.points_to_next_live:
                settings.SOUNDS["life"].play()
                self.lives = min(3, self.lives + 1)
                self.live_factor += 0.5
                self.points_to_next_live += settings.LIVE_POINTS_BASE * self.live_factor

            # Check growing up of the paddle
            if self.score >= self.points_to_next_grow_up:
                settings.SOUNDS["grow_up"].play()
                self.points_to_next_grow_up += (
                    settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
                )
                self.paddle.inc_size()

            # Chance to generate some powerup
            aux = random.random()
            if aux < 0.5:
                r = brick.get_collision_rect()
                aux = random.random()
                if aux < 0.3:
                    new_power_up = "TwoMoreBall"
                elif 0.3 <= aux <= 0.6:
                    new_power_up = "StickyPaddle"
                elif 0.6 <= aux <= 0.9:
                    new_power_up = "Cannons"
                else:
                    new_power_up = "Multiplier2x"
                self.powerups.append(
                        self.powerups_abstract_factory.get_factory(new_power_up).create (
                            r.centerx - 8, r.centery - 8
                        )
                )

        for i, projectile in enumerate(self.projectiles):
            projectile.update(dt)
            projectile.solve_world_boundaries()
            
            if not projectile.collides(self.brickset):
                if not projectile.vy:
                    if not i:
                        projectile.x = self.paddle.x - projectile.width
                    else:
                        projectile.x = self.paddle.x + self.paddle.width
                continue

            brick = self.brickset.get_colliding_brick(projectile.get_collision_rect())

            if brick is None:
                continue

            projectile.in_play = False
            brick.hit()
            self.score += brick.score()

        # Removing all balls that are not in play
        self.balls = [ball for ball in self.balls if ball.in_play]

        self.projectiles = [projectile for projectile in self.projectiles if projectile.in_play]

        self.brickset.update(dt)

        if not self.balls:
            self.lives -= 1
            if self.lives == 0:
                self.state_machine.change("game_over", score=self.score)
            else:
                self.paddle.dec_size()
                self.state_machine.change(
                    "serve",
                    level=self.level,
                    score=self.score,
                    lives=self.lives,
                    paddle=self.paddle,
                    brickset=self.brickset,
                    points_to_next_live=self.points_to_next_live,
                    live_factor=self.live_factor,
                )

        # Update powerups
        for powerup in self.powerups:
            powerup.update(dt)

            if powerup.collides(self.paddle):
                powerup.take(self)

        # Remove powerups that are not in play
        self.powerups = [p for p in self.powerups if p.in_play]

        # Check victory
        if self.brickset.size == 1 and next(
            (True for _, b in self.brickset.bricks.items() if b.broken), False
        ):
            self.state_machine.change(
                "victory",
                lives=self.lives,
                level=self.level,
                score=self.score,
                paddle=self.paddle,
                balls=self.balls,
                points_to_next_live=self.points_to_next_live,
                live_factor=self.live_factor,
            )
        
        if self.sticky or self.multiplier2x:
            self.counter += dt
            if self.counter >= self.timer:
                self.counter = 0
                self.sticky = False
                self.multiplier2x = False
                for ball in self.balls:
                    if ball.attached:
                        ball.vx = random.randint(-80, 80)
                        ball.vy = random.randint(-170, -100)
                        ball.attached = False
                    


    def render(self, surface: pygame.Surface) -> None:
        heart_x = settings.VIRTUAL_WIDTH - 120

        i = 0
        # Draw filled hearts
        while i < self.lives:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][0]
            )
            heart_x += 11
            i += 1

        # Draw empty hearts
        while i < 3:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][1]
            )
            heart_x += 11
            i += 1

        render_text(
            surface,
            f"Score: {self.score}",
            settings.FONTS["tiny"],
            settings.VIRTUAL_WIDTH - 80,
            5,
            (255, 255, 255),
        )

        self.brickset.render(surface)

        self.paddle.render(surface)

        for ball in self.balls:
            ball.render(surface)

        for projectile in self.projectiles:
            projectile.render(surface)

        for powerup in self.powerups:
            powerup.render(surface)
            
        if self.sticky:
            render_text(
                surface,
                f"Sticky paddle time: {int(10 - self.counter)}",
                settings.FONTS["small"],
                35,
                10,
                (255, 255, 255),
            )
        if self.multiplier2x:
            render_text(
                surface,
                f"2x score multiplier time: {int(10 - self.counter)}",
                settings.FONTS["small"],
                35,
                10,
                (255, 255, 255),
            )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "move_left":
            if input_data.pressed:
                self.paddle.vx = -settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx < 0:
                self.paddle.vx = 0
        elif input_id == "move_right":
            if input_data.pressed:
                self.paddle.vx = settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx > 0:
                self.paddle.vx = 0
        elif input_id == "pause" and input_data.pressed:
            self.state_machine.change(
                "pause",
                level=self.level,
                score=self.score,
                lives=self.lives,
                paddle=self.paddle,
                balls=self.balls,
                brickset=self.brickset,
                points_to_next_live=self.points_to_next_live,
                live_factor=self.live_factor,
                powerups=self.powerups,
                sticky=self.sticky,
                timer=self.timer,
                counter=self.counter,
            )
        elif input_id == "throw":
            for ball in self.balls:
                if ball.attached:    
                    ball.attached = False
                    settings.SOUNDS["paddle_hit"].play()
                    ball.vx = random.randint(-80, 80)
                    ball.vy = random.randint(-170, -100)
        elif input_id == "fire":
            for projectile in self.projectiles:
                projectile.vy = random.randint(-180, -130)
                projectile.texture = settings.TEXTURES["projectile"]
