#!/usr/bin/env python3
"""
Entry point module for the jimaku-dl package.
Allows running the package with 'python -m jimaku_dl' or just 'jimaku-dl'.
"""
import sys

from jimaku_dl.cli import main

if __name__ == "__main__":
    sys.exit(main())
