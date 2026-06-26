"""Load sample CSV via QuestDB-first pipeline (see scripts/setup_questdb_pipeline.py)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from setup_questdb_pipeline import main

if __name__ == "__main__":
    main()
