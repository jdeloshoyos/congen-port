"""Run the real pyglet event loop for a moment and exit (CI smoke test)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pyglet  # noqa: E402
from congen2.app import App  # noqa: E402


def main() -> None:
    app = App()
    pyglet.clock.schedule_once(lambda dt: app.close(), 1.0)
    pyglet.app.run(interval=1 / 120)
    print("event loop ok")


if __name__ == "__main__":
    main()
