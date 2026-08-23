"""Entry point for PyInstaller - runs dwatcher CLI as a module."""

import sys
from dwatcher.cli import main

if __name__ == "__main__":
    sys.exit(main())