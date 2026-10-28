"""Exercise the app state machine without waiting on real input."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import os
os.environ.setdefault("CONGEN2_USER_DIR", tempfile.mkdtemp(prefix="congen2-flow-"))

import pyglet  # noqa: E402
from pyglet.window import key  # noqa: E402

from congen2.app import App, CREDITS, LEVEL, MENU  # noqa: E402


def press(app, sym):
    app.keydelay = 0
    app.on_key_press(sym, 0)
    app._step()
    app.on_key_release(sym, 0)


app = App()
app.switch_to()
app.dispatch_events()

assert app.state == MENU
press(app, key.DOWN)
assert app.menuopt == 2, app.menuopt
press(app, key.RIGHT)
press(app, key.UP)
assert app.menuopt == 1, app.menuopt
press(app, key.ENTER)
assert app.state == LEVEL, app.state
assert app.world is not None

# Advance a little and draw a frame.
for _ in range(60):
    app._step()
app.on_draw()

# Pause, toggle music, open controls, rebind, back out, resume.
press(app, key.P)
assert app.paused
press(app, key.DOWN)                 # Musica
old_music = app.cfg.music_on
press(app, key.ENTER)
assert app.cfg.music_on != old_music
press(app, key.DOWN)                 # Sonido
press(app, key.DOWN)                 # Controles
assert app.pause_cursor == 3
press(app, key.ENTER)
assert app.controls_mode
press(app, key.ENTER)                # start rebinding first action
assert app.awaiting_key is not None
press(app, key.F)
assert app.cfg.bindings["up"] == "F", app.cfg.bindings
press(app, key.ESCAPE)               # leave controls
assert not app.controls_mode
press(app, key.P)                    # resume
assert not app.paused

# Abandon to menu via Escape.
press(app, key.ESCAPE)
assert app.state == MENU, app.state

# Force the credits screen.
app.state = CREDITS
press(app, key.ENTER)
assert app.state == MENU

print("flow ok")
app.close()
