"""Run the pinned, dependency-free SemDecide CLI without global installation."""
import sys
from integrations.kit import source

sys.path.insert(0, str(source('semdecide') / 'src'))
from reflex_guard.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
