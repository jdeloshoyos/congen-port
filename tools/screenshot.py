"""Render a few representative frames to PNG for visual verification.

Usage:
    uv run python tools/screenshot.py --state menu --out shots/menu.png
    uv run python tools/screenshot.py --state level --ticks 300 --out shots/level.png
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pyglet  # noqa: E402

from congen2.app import App  # noqa: E402
from congen2.world import Controls  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="menu", choices=["menu", "level", "credits", "pause"])
    ap.add_argument("--ticks", type=int, default=0)
    ap.add_argument("--out", default="shot.png")
    ap.add_argument("--level", type=int, default=1)
    ap.add_argument("--fire", action="store_true")
    ap.add_argument("--invincible", action="store_true")
    args = ap.parse_args()

    app = App()
    app.switch_to()
    app.dispatch_events()

    if args.state in ("level", "pause"):
        app._start_level(args.level)
        if args.invincible:
            app.world.player.invencible = 1
        for t in range(args.ticks):
            c = Controls(fire=args.fire, up=False, down=False, left=False, right=False)
            # gentle drift so entities are spread out
            if t % 80 < 40:
                c.left = True
            else:
                c.right = True
            app.world.tick(c)
            app.audio.play_all(app.world.sounds)
        app.alpha = 0.5
        if args.state == "pause":
            app.paused = True
    elif args.state == "credits":
        app.state = "credits"

    app.on_draw()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pyglet.image.get_buffer_manager().get_color_buffer().save(str(out))
    print("saved", out, "size", app.width, app.height)
    app.close()


if __name__ == "__main__":
    main()
