from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def get_md_files(input_dir: Path) -> list[Path]:
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".md"
    )


def move_extra_files(input_dir: Path, target_dir: Path, keep: int, dry_run: bool) -> None:
    files = get_md_files(input_dir)
    total = len(files)

    print(f"Input dir: {input_dir}")
    print(f"Target dir: {target_dir}")
    print(f"Total .md files: {total}")
    print(f"Keep first: {keep}")

    if total <= keep:
        print("No extra files to move.")
        return

    extra_files = files[keep:]
    print(f"Extra files to move: {len(extra_files)}")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for src in extra_files:
        dst = target_dir / src.name
        print(f"{'[DRY-RUN] ' if dry_run else ''}move: {src.name} -> {dst}")
        if dry_run:
            continue
        if dst.exists():
            raise FileExistsError(f"Target already exists: {dst}")
        shutil.move(str(src), str(dst))

    print("Done.")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    default_input_dir = base_dir / "extractor" / "input"
    default_target_dir = base_dir / "waitlist"

    parser = argparse.ArgumentParser(
        description="Keep only the first N markdown files in extractor/input and move extras to waitlist."
    )
    parser.add_argument("--input-dir", type=Path, default=default_input_dir)
    parser.add_argument("--target-dir", type=Path, default=default_target_dir)
    parser.add_argument("--keep", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    move_extra_files(
        input_dir=args.input_dir,
        target_dir=args.target_dir,
        keep=args.keep,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()