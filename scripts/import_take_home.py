"""Import the private employer data pack into an ignored local directory safely."""
from __future__ import annotations
import argparse
from pathlib import Path
import zipfile

EXPECTED = {"crm_export.csv", "gtm_events.json", "ai_answers.json", "ql_standard.md", "brand_context.md", "DATA_README.md"}
MAX_FILE_SIZE = 2_000_000


def import_pack(archive: Path, destination: Path) -> list[str]:
    if not archive.exists():
        raise FileNotFoundError(f"Take-home ZIP not found: {archive}")
    extracted: dict[str, bytes] = {}
    with zipfile.ZipFile(archive) as zf:
        for item in zf.infolist():
            if item.is_dir():
                continue
            parts = Path(item.filename.replace("\\", "/")).parts
            if len(parts) < 2 or parts[-2] != "data" or parts[-1] not in EXPECTED:
                continue
            if item.file_size > MAX_FILE_SIZE:
                raise ValueError(f"Source file is unexpectedly large: {parts[-1]}")
            if parts[-1] in extracted:
                raise ValueError(f"Duplicate data entry: {parts[-1]}")
            extracted[parts[-1]] = zf.read(item)
    missing = EXPECTED - extracted.keys()
    if missing:
        raise ValueError("Missing required data files: " + ", ".join(sorted(missing)))
    destination.mkdir(parents=True, exist_ok=True)
    # An individual file is written only after complete ZIP validation.
    for name, contents in sorted(extracted.items()):
        (destination / name).write_bytes(contents)
    return sorted(extracted)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Stargo synthetic take-home source into git-ignored data/private")
    parser.add_argument("zip", type=Path, help="Path to the original Stargo take-home ZIP")
    parser.add_argument("--dest", type=Path, default=Path(__file__).resolve().parents[1]/"data"/"private")
    args = parser.parse_args()
    imported = import_pack(args.zip, args.dest)
    print(f"Imported {len(imported)} private input files into {args.dest} (ignored by Git).")


if __name__ == "__main__":
    main()
