from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # Window
    W: int = 900
    H: int = 650
    FPS: int = 60

    # Gameplay tuning
    PLAYER_SPEED: float = 420.0
    PLAYER_FIRE_COOLDOWN: float = 0.22  # seconds (base)
    BULLET_SPEED: float = 900.0

    ENEMY_BASE_SPEED: float = 120.0
    ENEMY_HP: int = 1

    POWERUP_DROP_CHANCE: float = 0.18
    POWERUP_DURATION: float = 10.0

    # Difficulty scaling
    WAVE_TIME_BETWEEN: float = 2.0
    WAVE_SPEED_SCALER: float = 0.06
    WAVE_DENSITY_SCALER: float = 0.10

    # Colors (RGB)
    BG = (8, 10, 18)
    FG = (220, 230, 255)
    PLAYER = (70, 210, 255)
    ENEMY = (255, 100, 130)
    BULLET = (255, 240, 140)
    ENEMY_BULLET = (255, 160, 80)
    POWERUP = (140, 255, 140)
    SHIELD = (120, 170, 255)
