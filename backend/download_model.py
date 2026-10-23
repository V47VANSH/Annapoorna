"""Download the crop disease model (~300MB) from the GitHub release.

The weights are not stored in git, so a clone stays small. Run this once:

    python download_model.py            # writes backend/crop_disease_cnn_model.h5
    python download_model.py --force    # download again even if the file is fine

Uses only the standard library, so it works before `uv sync`.
"""

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

MODEL_URL = os.environ.get(
    "MODEL_URL",
    "https://github.com/V47VANSH/Annapoorna/releases/download/model-v1/"
    "crop_disease_cnn_model.h5",
)
MODEL_SHA256 = "91065b9fcaba6b2182f574d6a32f7f6244701bb5b91a6ff4ff117e4642a37aed"
MODEL_SIZE = 313318752

DEFAULT_PATH = Path(__file__).resolve().parent / "crop_disease_cnn_model.h5"
CHUNK = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _is_valid(path: Path) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == MODEL_SIZE
        and _sha256(path) == MODEL_SHA256
    )


def download(dest: Path, force: bool = False) -> None:
    if not force and _is_valid(dest):
        print(f"Model already present and verified: {dest}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    print(f"Downloading {MODEL_URL}")

    digest = hashlib.sha256()
    done = 0
    tty = sys.stdout.isatty()
    next_mark = 0.1
    with urllib.request.urlopen(MODEL_URL, timeout=60) as resp, part.open("wb") as out:
        total = int(resp.headers.get("Content-Length") or MODEL_SIZE)
        while chunk := resp.read(CHUNK):
            out.write(chunk)
            digest.update(chunk)
            done += len(chunk)
            if tty:
                print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)
            elif done / total >= next_mark:
                # build logs and pipes: one line per 10%
                print(f"  {done / 1e6:.0f} / {total / 1e6:.0f} MB", flush=True)
                next_mark += 0.1
    if tty:
        print()

    if digest.hexdigest() != MODEL_SHA256:
        part.unlink(missing_ok=True)
        sys.exit("Checksum mismatch, the download was corrupted. Try again.")

    part.replace(dest)
    print(f"Saved {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(os.environ.get("MODEL_PATH", DEFAULT_PATH)),
        help="where to save the file (default: MODEL_PATH or backend/)",
    )
    parser.add_argument("--force", action="store_true", help="re-download")
    args = parser.parse_args()
    download(args.dest, args.force)


if __name__ == "__main__":
    main()
