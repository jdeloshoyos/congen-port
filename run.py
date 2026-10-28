"""Entry point for the Congeneration 2 port.

    uv run python run.py [--data PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running straight from a checkout without installing the package.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pyglet  # noqa: E402

from congen2.app import App  # noqa: E402
from congen2.constants import MAX_FPS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Congeneration 2 (port)")
    parser.add_argument("--data", default=None,
                        help="directory containing the original CG2 data files")
    args = parser.parse_args()

    App(data_directory=args.data)
    pyglet.app.run(interval=1.0 / MAX_FPS)


if __name__ == "__main__":
    main()
