"""Launch from a checkout or as the PyInstaller entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from warcraft_survivors.launch import main  # noqa: E402

if __name__ == "__main__":
    main()
