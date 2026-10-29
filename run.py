"""Entry point for the Congeneration 2 port.

    uv run python run.py [--data PATH] [--scale N] [--auto-scale]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running straight from a checkout without installing the package.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from congen2.app import main  # noqa: E402


if __name__ == "__main__":
    main()
