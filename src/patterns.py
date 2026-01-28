import math
import random
from dataclasses import dataclass
from typing import Callable, List, Tuple

Vec2 = Tuple[float, float]


@dataclass
class SpawnSpec:
    # x,y are spawn positions; move_fn defines movement over time; meta can include enemy type
    x: float
    y: float
    move_fn: Callable[[float, float, float], Vec2]  # (t, x0, y0) -> (x, y)
    fire_profile: str = "basic"  # reserved for future


def line_pattern(count: int, width: float, y: float, x_center: float, speed: float) -> List[SpawnSpec]:
    # Straight downward line of enemies spaced across a width
    if count <= 1:
        xs = [x_center]
    else:
        xs = [x_center - width / 2 + i * (width / (count - 1)) for i in range(count)]

    def mk_move_fn(v):
        return lambda t, x0, y0: (x0, y0 + v * t)

    return [SpawnSpec(x=x, y=y, move_fn=mk_move_fn(speed)) for x in xs]


def v_pattern(count: int, spread: float, y: float, x_center: float, speed: float) -> List[SpawnSpec]:
    # V formation that drifts down
    # count should be odd ideally; we'll handle even counts.
    half = max(1, count // 2)
    specs = []
    for i in range(count):
        offset = (i - (count - 1) / 2.0)
        x = x_center + offset * (spread / max(1, half))
        y_i = y + abs(offset) * 14  # slight vertical offset for V shape

        def move_fn_factory():
            v = speed
            wobble = random.uniform(18.0, 34.0)
            phase = random.uniform(0, math.tau)
            return lambda t, x0, y0: (x0 + math.sin(t * 1.6 + phase) * wobble, y0 + v * t)

        specs.append(SpawnSpec(x=x, y=y_i, move_fn=move_fn_factory()))
    return specs


def sine_drift_pattern(count: int, span: float, y: float, x_center: float, speed: float) -> List[SpawnSpec]:
    # Enemies drift down while oscillating horizontally with different phases
    specs = []
    for i in range(count):
        x = x_center - span / 2 + (i + 0.5) * (span / count)
        amp = random.uniform(40.0, 90.0)
        freq = random.uniform(1.0, 2.2)
        phase = random.uniform(0, math.tau)

        def mf_factory(amp=amp, freq=freq, phase=phase, v=speed):
            return lambda t, x0, y0: (x0 + math.sin(t * freq + phase) * amp, y0 + v * t)

        specs.append(SpawnSpec(x=x, y=y, move_fn=mf_factory()))
    return specs


def ring_pattern(count: int, radius: float, y: float, x_center: float, speed: float) -> List[SpawnSpec]:
    # Spawn enemies around a ring that slowly collapses as it moves down
    specs = []
    for i in range(count):
        ang = (i / count) * math.tau
        x = x_center + math.cos(ang) * radius
        y_i = y + math.sin(ang) * (radius * 0.35)

        def mf_factory(ang=ang, r=radius, v=speed):
            # Spiral in slightly while moving down
            shrink = random.uniform(0.05, 0.12)
            return lambda t, x0, y0: (
                x_center + math.cos(ang + t * 0.5) * (r * (1.0 - shrink * t)),
                y0 + v * t
            )

        specs.append(SpawnSpec(x=x, y=y_i, move_fn=mf_factory()))
    return specs


def random_pattern(wave_index: int, screen_w: int, speed: float) -> List[SpawnSpec]:
    # Pick a pattern based on wave index, with mild randomness.
    x_center = screen_w / 2
    y = -40.0
    # density increases with wave
    base = 6 + int(wave_index * 0.8)
    count = min(18, base + random.randint(-1, 3))

    choice = random.choice(["line", "v", "sine", "ring"] if wave_index >= 3 else ["line", "v", "sine"])
    if choice == "line":
        return line_pattern(count=count, width=min(700, 300 + wave_index * 25), y=y, x_center=x_center, speed=speed)
    if choice == "v":
        return v_pattern(count=count, spread=min(650, 260 + wave_index * 22), y=y, x_center=x_center, speed=speed)
    if choice == "ring":
        return ring_pattern(count=min(14, max(8, count)), radius=min(220, 110 + wave_index * 10), y=y + 20, x_center=x_center, speed=speed)
    return sine_drift_pattern(count=count, span=min(760, 320 + wave_index * 28), y=y, x_center=x_center, speed=speed)
