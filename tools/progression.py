"""Drive a full playthrough (both levels -> credits) headlessly through App."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["CONGEN2_USER_DIR"] = tempfile.mkdtemp(prefix="congen2-prog-")

import pyglet  # noqa: E402

from congen2.app import App, CREDITS, LEVEL  # noqa: E402


def force_boss_kill(app: App) -> None:
    """Advance until the boss patrols, then mark all sections destroyed."""
    w = app.world
    for _ in range(4500):
        app._step()
        if app.state != LEVEL:
            return
        if any(9 < e.kind < 16 for e in w.enemies) and w.enemies[0].y <= 20:
            break
    for i, e in enumerate(w.enemies[:6]):
        e.kind = 16 + i
        e.health = 1


def run() -> None:
    app = App()
    app.switch_to()
    app.dispatch_events()
    app._start_level(1)
    assert app.state == LEVEL
    app.world.player.invencible = 1

    force_boss_kill(app)
    for _ in range(600):
        app._step()
        if app.state != LEVEL:
            break
    print("after level 1:", app.state, "mapnumber", app.mapnumber,
          "maxlevel", app.save.max_level_reached, "score", app.save.max_score)
    assert app.state == LEVEL, app.state
    assert app.mapnumber == 2

    app.world.player.invencible = 1
    force_boss_kill(app)
    for _ in range(600):
        app._step()
        if app.state != LEVEL:
            break
    print("after level 2:", app.state, "maxlevel", app.save.max_level_reached)
    assert app.state == CREDITS, app.state
    print("progression ok")
    app.close()


if __name__ == "__main__":
    run()
