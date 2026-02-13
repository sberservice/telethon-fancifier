from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    src_path = str(src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from telethon_fancifier.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()