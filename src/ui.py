import pygame

class HUD:
    def __init__(self, settings):
        self.settings = settings
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_big = pygame.font.SysFont("consolas", 34, bold=True)

    def draw(self, surf, score, wave, lives, multiplier, powerup_text, paused=False):
        s = self.settings
        # Top bar text
        left = f"Score: {score:,}"
        mid = f"Wave: {wave}"
        right = f"Lives: {lives}   x{multiplier:.1f}"

        tl = self.font.render(left, True, s.FG)
        tm = self.font.render(mid, True, s.FG)
        tr = self.font.render(right, True, s.FG)

        surf.blit(tl, (18, 12))
        surf.blit(tm, (s.W / 2 - tm.get_width() / 2, 12))
        surf.blit(tr, (s.W - tr.get_width() - 18, 12))

        if powerup_text:
            pu = self.font.render(powerup_text, True, (190, 255, 190))
            surf.blit(pu, (18, 38))

        if paused:
            msg = self.font_big.render("PAUSED", True, s.FG)
            surf.blit(msg, (s.W / 2 - msg.get_width() / 2, s.H / 2 - msg.get_height() / 2))
