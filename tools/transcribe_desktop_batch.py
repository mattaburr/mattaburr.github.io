#!/usr/bin/env python3
"""Batch transcribe Desktop/Input media with local WhisperX diarization.

Defaults are intentionally desktop-friendly:
  input:  ~/Desktop/Input
  output: ~/Desktop/Output
  model:  small.en

Diarization uses pyannote models through WhisperX and requires a Hugging Face
access token with the required model terms accepted.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote

MEDIA_EXTS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma",
    ".aif", ".aiff", ".amr", ".m4b",
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".mpg", ".mpeg",
    ".wmv", ".flv", ".3gp",
}

HTML_EXTS = {".html", ".htm"}


def desktop_path(folder_name: str) -> Path:
    return Path.home() / "Desktop" / folder_name


def find_media_links_in_html(html_file: Path) -> list[Path]:
    """Return local audio/video files referenced by an HTML file."""
    try:
        text = html_file.read_text(errors="ignore")
    except OSError:
        return []

    found: list[Path] = []
    links = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', text, flags=re.IGNORECASE)

    for raw_link in links:
        link = unquote(html.unescape(raw_link).strip())
        if not link:
            continue

        lower_link = link.lower()
        if lower_link.startswith(("data:", "http://", "https://", "javascript:", "mailto:", "blob:")):
            continue

        link = link.split("#", 1)[0].split("?", 1)[0].strip()
        if not link or len(link) > 500:
            continue

        try:
            possible_path = (html_file.parent / link).resolve()
        except OSError:
            continue

        if possible_path.exists() and possible_path.suffix.lower() in MEDIA_EXTS:
            found.append(possible_path)

    return found


def unzip_archives(input_dir: Path) -> None:
    for zip_path in sorted(input_dir.rglob("*.zip")):
        if not zip_path.is_file() or zip_path.name.startswith("."):
            continue

        extract_dir = zip_path.parent / zip_path.stem
        extract_dir.mkdir(parents=True, exist_ok=True)
        print(f"Unzipping: {zip_path}")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile as exc:
            print(f"Warning: could not unzip {zip_path}: {exc}", file=sys.stderr)


def find_media_files(input_dir: Path) -> list[Path]:
    media_files: set[Path] = set()

    for path in input_dir.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue

        suffix = path.suffix.lower()
        if suffix in MEDIA_EXTS:
            media_files.add(path.resolve())
        elif suffix in HTML_EXTS:
            media_files.update(link.resolve() for link in find_media_links_in_html(path))

    return sorted(media_files)


def run_whisperx(media_path: Path, args: argparse.Namespace, hf_token: str) -> int:
    whisperx_bin = shutil.which("whisperx") or "whisperx"
    command = [
        whisperx_bin,
        str(media_path),
        "--model", args.model,
        "--language", args.language,
        "--diarize",
        "--min_speakers", str(args.min_speakers),
        "--max_speakers", str(args.max_speakers),
        "--output_format", "txt",
        "--output_dir", str(args.output_dir),
    ]

    if hf_token:
        command.extend(["--hf_token", hf_token])
    if args.device:
        command.extend(["--device", args.device])
    if args.compute_type:
        command.extend(["--compute_type", args.compute_type])

    print("\n========================================")
    print(f"Processing: {media_path.name}")
    print("========================================")
    return subprocess.run(command, check=False).returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch transcribe ~/Desktop/Input media into ~/Desktop/Output text files with WhisperX diarization.",
    )
    parser.add_argument("--input-dir", type=Path, default=desktop_path("Input"), help="Folder containing audio/video files.")
    parser.add_argument("--output-dir", type=Path, default=desktop_path("Output"), help="Folder for transcript .txt files.")
    parser.add_argument("--model", default="small.en", help="Whisper model to use; small.en is the small English model.")
    parser.add_argument("--language", default="en", help="Language code passed to WhisperX.")
    parser.add_argument("--min-speakers", default=2, type=int, help="Minimum number of speakers for diarization.")
    parser.add_argument("--max-speakers", default=2, type=int, help="Maximum number of speakers for diarization.")
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"), help="Hugging Face token; defaults to the HF_TOKEN environment variable.")
    parser.add_argument("--device", default=None, help="Optional WhisperX device override, for example cpu or cuda.")
    parser.add_argument("--compute-type", default=None, help="Optional WhisperX compute type, for example int8 on CPU.")
    parser.add_argument("--unzip", action="store_true", help="Extract .zip files found under the input folder before scanning.")
    parser.add_argument("--offline", action="store_true", help="Use only locally cached models; no network calls for model downloads.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.input_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.offline:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    if not args.hf_token and not args.offline:
        print("Error: diarization requires a Hugging Face token for first-time model access. Set HF_TOKEN, pass --hf-token, or use --offline after models are cached locally.", file=sys.stderr)
        return 2

    if args.unzip:
        unzip_archives(args.input_dir)

    media_files = find_media_files(args.input_dir)
    print("\nMedia files found:")
    if not media_files:
        print(f"No audio/video files were found in {args.input_dir}.")
        return 1

    for media_file in media_files:
        print(f" - {media_file}")

    successful = 0
    failed = 0
    for media_file in media_files:
        if run_whisperx(media_file, args, args.hf_token) == 0:
            successful += 1
            print(f"Finished: {media_file.name}")
        else:
            failed += 1
            print(f"Failed: {media_file.name}")

    print("\n========================================")
    print("DONE")
    print("========================================")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output folder: {args.output_dir}")

    txt_files = sorted(args.output_dir.rglob("*.txt"))
    print("\nTXT transcript files:")
    if txt_files:
        for txt_file in txt_files:
            print(txt_file)
    else:
        print("No .txt files found.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
