import math
import random
from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

Vec2 = pygame.math.Vector2


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


@dataclass
class Bullet:
    pos: Vec2
    vel: Vec2
    radius: int
    friendly: bool
    damage: int = 1

    def update(self, dt: float):
        self.pos += self.vel * dt

    def rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surf, settings):
        color = settings.BULLET if self.friendly else settings.ENEMY_BULLET
        pygame.draw.circle(surf, color, (int(self.pos.x), int(self.pos.y)), self.radius)


class Player:
    def __init__(self, settings):
        self.settings = settings
        self.pos = Vec2(settings.W / 2, settings.H - 70)
        self.vel = Vec2(0, 0)
        self.radius = 18
        self.lives = 3

        # Power-up state
        self.shield = 0.0
        self.spread = 0.0
        self.rapid = 0.0

        self.fire_cd = 0.0

    def is_alive(self):
        return self.lives > 0

    def fire_cooldown(self):
        base = self.settings.PLAYER_FIRE_COOLDOWN
        if self.rapid > 0:
            base *= 0.55
        return base

    def update(self, dt: float, keys):
        s = self.settings
        move = Vec2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move.y += 1

        if move.length_squared() > 0:
            move = move.normalize()

        self.pos += move * s.PLAYER_SPEED * dt
        self.pos.x = clamp(self.pos.x, 30, s.W - 30)
        self.pos.y = clamp(self.pos.y, s.H * 0.55, s.H - 30)

        self.fire_cd = max(0.0, self.fire_cd - dt)

        # tick power-ups
        self.shield = max(0.0, self.shield - dt)
        self.spread = max(0.0, self.spread - dt)
        self.rapid = max(0.0, self.rapid - dt)

    def can_fire(self):
        return self.fire_cd <= 0.0

    def shoot(self):
        self.fire_cd = self.fire_cooldown()
        bullets = []
        base_vel = Vec2(0, -self.settings.BULLET_SPEED)
        if self.spread > 0:
            # 3-shot spread
            for ang in (-14, 0, 14):
                v = base_vel.rotate(ang)
                bullets.append(Bullet(pos=self.pos.copy() + Vec2(0, -22), vel=v, radius=4, friendly=True))
        else:
            bullets.append(Bullet(pos=self.pos.copy() + Vec2(0, -22), vel=base_vel, radius=4, friendly=True))
        return bullets

    def hit(self):
        if self.shield > 0:
            # shield absorbs
            self.shield = 0.0
            return False
        self.lives -= 1
        # brief invuln via shield-like effect
        self.shield = 1.1
        return True

    def draw(self, surf):
        s = self.settings
        # player ship (triangle-ish)
        p = (int(self.pos.x), int(self.pos.y))
        pts = [
            (p[0], p[1] - 22),
            (p[0] - 18, p[1] + 18),
            (p[0] + 18, p[1] + 18),
        ]
        pygame.draw.polygon(surf, s.PLAYER, pts)
        pygame.draw.polygon(surf, (20, 30, 50), pts, 2)

        if self.shield > 0:
            alpha = int(120 + 80 * math.sin(pygame.time.get_ticks() * 0.01))
            # Draw shield ring
            pygame.draw.circle(surf, s.SHIELD, p, 30, 2)


class Enemy:
    def __init__(self, settings, x: float, y: float, move_fn, hp: int = 1):
        self.settings = settings
        self.spawn = Vec2(x, y)
        self.pos = Vec2(x, y)
        self.move_fn = move_fn
        self.t = 0.0
        self.radius = 16
        self.hp = hp

        # Simple behavior state machine:
        # ENTER -> (OPTIONAL) ATTACK -> EXIT
        self.state = "enter"
        self.attack_timer = random.uniform(1.2, 3.0)
        self.exit_timer = random.uniform(7.0, 12.0)

        self.fire_cd = random.uniform(0.8, 1.9)

    def alive(self):
        return self.hp > 0

    def update(self, dt: float, wave_speed_bonus: float):
        self.t += dt
        self.fire_cd = max(0.0, self.fire_cd - dt)

        # state transitions
        self.attack_timer -= dt
        self.exit_timer -= dt
        if self.state == "enter" and self.t > 0.35:
            self.state = "patrol"
        if self.state in ("enter", "patrol") and self.attack_timer <= 0:
            self.state = "attack"
            self.attack_timer = random.uniform(3.2, 5.0)
        if self.exit_timer <= 0:
            self.state = "exit"

        # movement
        x, y = self.move_fn(self.t, self.spawn.x, self.spawn.y)
        self.pos.x, self.pos.y = x, y

        if self.state == "attack":
            # add a brief dive toward player area
            self.pos.y += (120 + 40 * wave_speed_bonus) * dt
        elif self.state == "exit":
            self.pos.y += (160 + 60 * wave_speed_bonus) * dt

    def maybe_fire(self):
        # Modest enemy shooting: downwards with small horizontal randomness
        if self.fire_cd > 0:
            return None
        self.fire_cd = random.uniform(1.0, 2.2)
        vx = random.uniform(-70.0, 70.0)
        return Bullet(pos=self.pos.copy() + Vec2(0, 18), vel=Vec2(vx, 420.0), radius=4, friendly=False)

    def damage(self, n=1):
        self.hp -= n

    def rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surf):
        s = self.settings
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, s.ENEMY, p, self.radius)
        # eye
        pygame.draw.circle(surf, (20, 20, 30), (p[0] - 5, p[1] - 3), 4)
        pygame.draw.circle(surf, (20, 20, 30), (p[0] + 6, p[1] - 3), 4)
        # outline
        pygame.draw.circle(surf, (60, 20, 30), p, self.radius, 2)


class PowerUp:
    # Types
    SPREAD = "spread"
    RAPID = "rapid"
    SHIELD = "shield"
    MULTI = "multiplier"

    def __init__(self, settings, x: float, y: float, kind: str):
        self.settings = settings
        self.pos = Vec2(x, y)
        self.kind = kind
        self.radius = 12
        self.vel = Vec2(0, 140.0)
        self.t = 0.0

    def update(self, dt: float):
        self.t += dt
        self.pos += self.vel * dt
        # small sway
        self.pos.x += math.sin(self.t * 4.0) * 18.0 * dt

    def rect(self):
        r = self.radius
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), r * 2, r * 2)

    def draw(self, surf):
        s = self.settings
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, s.POWERUP, p, self.radius)
        # inner icon
        if self.kind == self.SPREAD:
            pygame.draw.line(surf, (20, 40, 20), (p[0]-6, p[1]+3), (p[0], p[1]-6), 2)
            pygame.draw.line(surf, (20, 40, 20), (p[0]+6, p[1]+3), (p[0], p[1]-6), 2)
        elif self.kind == self.RAPID:
            pygame.draw.line(surf, (20, 40, 20), (p[0]-6, p[1]+6), (p[0]+6, p[1]-6), 2)
        elif self.kind == self.SHIELD:
            pygame.draw.circle(surf, (20, 40, 20), p, 6, 2)
        else:
            pygame.draw.circle(surf, (20, 40, 20), p, 5)
            pygame.draw.line(surf, (20, 40, 20), (p[0], p[1]-8), (p[0], p[1]+8), 2)
