import random
import pygame

from .entities import Player, Enemy, PowerUp
from .patterns import random_pattern
from .ui import HUD


class Starfield:
    def __init__(self, settings, count=160):
        self.settings = settings
        self.stars = []
        for _ in range(count):
            x = random.uniform(0, settings.W)
            y = random.uniform(0, settings.H)
            sp = random.uniform(30, 150)
            r = random.choice([1, 1, 2])
            self.stars.append([x, y, sp, r])

    def update(self, dt):
        s = self.settings
        for st in self.stars:
            st[1] += st[2] * dt
            if st[1] > s.H:
                st[0] = random.uniform(0, s.W)
                st[1] = -2
                st[2] = random.uniform(30, 150)
                st[3] = random.choice([1, 1, 2])

    def draw(self, surf):
        for x, y, _, r in self.stars:
            pygame.draw.circle(surf, (160, 170, 200), (int(x), int(y)), r)


class WaveManager:
    def __init__(self, settings):
        self.settings = settings
        self.wave_index = 0
        self.time_to_next = 1.0
        self.spawn_queue = []  # list[dict] with spawn info
        self.total_spawned_this_wave = 0

    def next_wave(self):
        s = self.settings
        self.wave_index += 1
        self.total_spawned_this_wave = 0
        # speed increases each wave
        speed = s.ENEMY_BASE_SPEED * (1.0 + s.WAVE_SPEED_SCALER * (self.wave_index - 1))
        specs = random_pattern(self.wave_index, s.W, speed=speed)
        # Stagger spawns for readability
        for i, sp in enumerate(specs):
            self.spawn_queue.append({"delay": i * 0.08, "spec": sp})
        self.time_to_next = s.WAVE_TIME_BETWEEN

    def update(self, dt, enemies):
        # if no queue and no enemies => start next wave after delay
        if not self.spawn_queue and not enemies:
            self.time_to_next -= dt
            if self.time_to_next <= 0:
                self.next_wave()

        # process spawn queue
        for item in self.spawn_queue:
            item["delay"] -= dt
        ready = [it for it in self.spawn_queue if it["delay"] <= 0]
        self.spawn_queue = [it for it in self.spawn_queue if it["delay"] > 0]

        for it in ready:
            sp = it["spec"]
            enemies.append(Enemy(self.settings, sp.x, sp.y, sp.move_fn, hp=self.settings.ENEMY_HP))
            self.total_spawned_this_wave += 1

    def difficulty_bonus(self):
        # returns a small scalar used for enemy exit/attack speed and point scaling
        return max(0.0, (self.wave_index - 1) * 0.25)


class PlayState:
    def __init__(self, settings, on_game_over):
        self.settings = settings
        self.on_game_over = on_game_over

        self.starfield = Starfield(settings)
        self.player = Player(settings)
        self.hud = HUD(settings)

        self.enemies = []
        self.bullets = []
        self.powerups = []

        self.wave_mgr = WaveManager(settings)
        self.wave_mgr.next_wave()

        self.score = 0
        self.multiplier = 1.0
        self.multiplier_timer = 0.0
        self.powerup_text = ""

        self.paused = False
        self.flash = 0.0  # hit flash

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = not self.paused

    def apply_powerup(self, kind: str):
        s = self.settings
        self.powerup_text = ""
        if kind == PowerUp.SPREAD:
            self.player.spread = s.POWERUP_DURATION
            self.powerup_text = "Power-up: Spread Shot"
        elif kind == PowerUp.RAPID:
            self.player.rapid = s.POWERUP_DURATION
            self.powerup_text = "Power-up: Rapid Fire"
        elif kind == PowerUp.SHIELD:
            self.player.shield = max(self.player.shield, s.POWERUP_DURATION * 0.6)
            self.powerup_text = "Power-up: Shield"
        else:
            self.multiplier = min(6.0, self.multiplier * 2.0)
            self.multiplier_timer = s.POWERUP_DURATION
            self.powerup_text = f"Power-up: Score x{self.multiplier:.1f}"

    def maybe_drop_powerup(self, x, y):
        if random.random() > self.settings.POWERUP_DROP_CHANCE:
            return
        kind = random.choices(
            [PowerUp.SPREAD, PowerUp.RAPID, PowerUp.SHIELD, PowerUp.MULTI],
            weights=[0.32, 0.26, 0.22, 0.20],
            k=1
        )[0]
        self.powerups.append(PowerUp(self.settings, x, y, kind))

    def update(self, dt):
        s = self.settings
        keys = pygame.key.get_pressed()

        if self.paused:
            self.starfield.update(dt * 0.15)
            return

        self.starfield.update(dt)

        self.player.update(dt, keys)

        # Shooting
        if keys[pygame.K_SPACE] and self.player.can_fire():
            self.bullets.extend(self.player.shoot())

        # Waves
        self.wave_mgr.update(dt, self.enemies)
        wave_bonus = self.wave_mgr.difficulty_bonus()

        # Enemies
        for e in self.enemies:
            e.update(dt, wave_speed_bonus=wave_bonus)
            b = e.maybe_fire()
            if b:
                self.bullets.append(b)

        # Bullets and powerups
        for b in self.bullets:
            b.update(dt)
        for pu in self.powerups:
            pu.update(dt)

        # Timers
        self.flash = max(0.0, self.flash - dt)
        if self.multiplier_timer > 0:
            self.multiplier_timer -= dt
            if self.multiplier_timer <= 0:
                self.multiplier = 1.0
        if self.powerup_text:
            # fade out message after ~2.5s
            # simplest: store as timer by trimming with multiplier_timer? keep separate
            pass

        # Collisions
        self.resolve_collisions()

        # Cleanup off-screen
        self.bullets = [b for b in self.bullets if -50 < b.pos.y < s.H + 80 and -60 < b.pos.x < s.W + 60]
        self.enemies = [e for e in self.enemies if e.alive() and e.pos.y < s.H + 80]
        self.powerups = [p for p in self.powerups if p.pos.y < s.H + 40]

        if not self.player.is_alive():
            self.on_game_over(self.score)

    def resolve_collisions(self):
        s = self.settings
        # Player bullets -> enemies
        for b in [bb for bb in self.bullets if bb.friendly]:
            br = b.rect()
            for e in self.enemies:
                if e.alive() and br.colliderect(e.rect()):
                    e.damage(b.damage)
                    b.pos.y = -10_000  # remove bullet
                    if not e.alive():
                        pts = int(100 * (1.0 + 0.06 * self.wave_mgr.wave_index) * self.multiplier)
                        self.score += pts
                        self.maybe_drop_powerup(e.pos.x, e.pos.y)
                    break

        # Enemy bullets -> player
        pr = pygame.Rect(int(self.player.pos.x - self.player.radius), int(self.player.pos.y - self.player.radius),
                         self.player.radius * 2, self.player.radius * 2)

        for b in [bb for bb in self.bullets if not bb.friendly]:
            if b.rect().colliderect(pr):
                b.pos.y = -10_000
                took_damage = self.player.hit()
                if took_damage:
                    self.flash = 0.18

        # Player -> powerup
        for pu in self.powerups:
            if pu.rect().colliderect(pr):
                self.apply_powerup(pu.kind)
                pu.pos.y = 10_000

        # Player -> enemy collision (ram)
        for e in self.enemies:
            if e.rect().colliderect(pr):
                e.hp = 0
                took_damage = self.player.hit()
                if took_damage:
                    self.flash = 0.18
                # points for risky ram
                self.score += int(60 * self.multiplier)

    def render(self, surf):
        s = self.settings
        surf.fill(s.BG)
        self.starfield.draw(surf)

        # bullets
        for b in self.bullets:
            b.draw(surf, s)

        # enemies
        for e in self.enemies:
            e.draw(surf)

        # powerups
        for pu in self.powerups:
            pu.draw(surf)

        # player
        if self.player.is_alive():
            self.player.draw(surf)

        # HUD
        self.hud.draw(
            surf,
            score=self.score,
            wave=self.wave_mgr.wave_index,
            lives=self.player.lives,
            multiplier=self.multiplier,
            powerup_text=self.powerup_text,
            paused=self.paused
        )

        if self.flash > 0:
            overlay = pygame.Surface((s.W, s.H), pygame.SRCALPHA)
            overlay.fill((255, 80, 90, int(120 * (self.flash / 0.18))))
            surf.blit(overlay, (0, 0))


class MenuState:
    def __init__(self, settings, on_start):
        self.settings = settings
        self.on_start = on_start
        self.starfield = Starfield(settings, count=190)
        self.font_title = pygame.font.SysFont("consolas", 54, bold=True)
        self.font = pygame.font.SysFont("consolas", 20)
        self.blink = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_start()
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        self.starfield.update(dt)
        self.blink += dt

    def render(self, surf):
        s = self.settings
        surf.fill(s.BG)
        self.starfield.draw(surf)

        title = self.font_title.render("GALACTIC TRAVELER", True, s.FG)
        surf.blit(title, (s.W/2 - title.get_width()/2, 150))

        sub = self.font.render("Waves • Patterns • Power-ups • Multipliers", True, (190, 200, 230))
        surf.blit(sub, (s.W/2 - sub.get_width()/2, 225))

        if (int(self.blink * 2) % 2) == 0:
            msg = self.font.render("Press ENTER to Start", True, s.FG)
            surf.blit(msg, (s.W/2 - msg.get_width()/2, 330))

        hint = self.font.render("Move: WASD/Arrows   Shoot: Space   Pause: P/Esc   Quit: Q", True, (160, 170, 200))
        surf.blit(hint, (s.W/2 - hint.get_width()/2, s.H - 90))


class GameOverState:
    def __init__(self, settings, score, on_restart):
        self.settings = settings
        self.score = score
        self.on_restart = on_restart
        self.starfield = Starfield(settings, count=170)
        self.font_title = pygame.font.SysFont("consolas", 56, bold=True)
        self.font = pygame.font.SysFont("consolas", 22)
        self.blink = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_restart()
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        self.starfield.update(dt)
        self.blink += dt

    def render(self, surf):
        s = self.settings
        surf.fill(s.BG)
        self.starfield.draw(surf)

        title = self.font_title.render("GAME OVER", True, (255, 140, 160))
        surf.blit(title, (s.W/2 - title.get_width()/2, 170))

        sc = self.font.render(f"Final Score: {self.score:,}", True, s.FG)
        surf.blit(sc, (s.W/2 - sc.get_width()/2, 260))

        if (int(self.blink * 2) % 2) == 0:
            msg = self.font.render("Press ENTER to Play Again", True, s.FG)
            surf.blit(msg, (s.W/2 - msg.get_width()/2, 330))

        hint = self.font.render("Quit: Q / Esc", True, (160, 170, 200))
        surf.blit(hint, (s.W/2 - hint.get_width()/2, s.H - 90))


class Game:
    def __init__(self, settings):
        self.settings = settings
        self.state = None
        self.best_score = 0

        self.to_menu()

    def to_menu(self):
        self.state = MenuState(self.settings, on_start=self.to_play)

    def to_play(self):
        self.state = PlayState(self.settings, on_game_over=self.to_game_over)

    def to_game_over(self, score):
        self.best_score = max(self.best_score, score)
        self.state = GameOverState(self.settings, score=score, on_restart=self.to_play)

    def handle_event(self, event):
        if self.state:
            self.state.handle_event(event)

    def update(self, dt):
        if self.state:
            self.state.update(dt)

    def render(self, surf):
        if self.state:
            self.state.render(surf)
