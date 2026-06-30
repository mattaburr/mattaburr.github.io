# Local WhisperX transcription workflow

This repository includes `tools/transcribe_desktop_batch.py`, a reusable desktop batch runner for local WhisperX transcription plus speaker diarization.

## Folder layout

Create these folders on your computer:

```text
Desktop/
  Input/   Put audio/video files here.
  Output/  Transcript .txt files are written here.
```

Supported input includes common audio and video files such as `.mp3`, `.wav`, `.m4a`, `.mp4`, `.mov`, `.mkv`, and `.webm`. The script can also scan local HTML exports for referenced media files, and can optionally unzip archives before scanning.

## One-time setup

Install FFmpeg, Python, and WhisperX in a virtual environment. On macOS with Homebrew:

```bash
brew install ffmpeg python
python3 -m venv ~/.venvs/whisperx
source ~/.venvs/whisperx/bin/activate
python -m pip install --upgrade pip
python -m pip install git+https://github.com/m-bain/whisperx.git
```

For diarization, create a Hugging Face access token and accept the required pyannote model terms. Save the token in your shell profile so you do not need to paste it every time:

```bash
export HF_TOKEN="paste-your-token-here"
```

## Batch transcription

Put files in `~/Desktop/Input`, activate the virtual environment, and run:

```bash
source ~/.venvs/whisperx/bin/activate
python tools/transcribe_desktop_batch.py
```

The default model is `small.en`, the small English Whisper model. The default diarization range is exactly two speakers, which is useful for two-person calls.

## Common options

```bash
# Extract any ZIP files in Desktop/Input before transcribing.
python tools/transcribe_desktop_batch.py --unzip

# Allow one to four speakers.
python tools/transcribe_desktop_batch.py --min-speakers 1 --max-speakers 4

# CPU-friendly run if your computer does not have a CUDA GPU.
python tools/transcribe_desktop_batch.py --device cpu --compute-type int8

# Use custom folders.
python tools/transcribe_desktop_batch.py --input-dir /path/to/Input --output-dir /path/to/Output
```

## Notes

- Diarization will fail without a valid Hugging Face token.
- WhisperX writes text transcripts into `~/Desktop/Output` by default.
- Keep original media files in `Desktop/Input`; the script does not delete input or output files.
