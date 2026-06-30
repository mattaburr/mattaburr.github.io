# Local WhisperX transcription workflow

This repository includes `tools/transcribe_desktop_batch.py`, a reusable desktop batch runner for local WhisperX transcription plus speaker diarization.

## What “hardware only, locally” means

The transcription and diarization work runs on your own computer, not in Google Colab or a cloud transcription service. There is one important practical detail: the first setup run must download WhisperX, the Whisper model, and the diarization model files. After those files are installed and cached on your machine, you can run the workflow with `--offline` so the script uses only local files.

## Folder layout

Create these folders on your computer:

```text
Desktop/
  Input/   Put audio/video files here.
  Output/  Transcript .txt files are written here.
```

Supported input includes common audio and video files such as `.mp3`, `.wav`, `.m4a`, `.mp4`, `.mov`, `.mkv`, and `.webm`. The script can also scan local HTML exports for referenced media files, and can optionally unzip archives before scanning.

## One-time setup with internet access

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

## First local run to populate your model cache

Before trying to run fully offline, put one short test audio/video file in `~/Desktop/Input` and run this once while you still have internet access:

```bash
source ~/.venvs/whisperx/bin/activate
python tools/transcribe_desktop_batch.py --device cpu --compute-type int8
```

That first run downloads and caches the needed model files locally. The default model is `small.en`, the small English Whisper model. The default diarization range is exactly two speakers, which is useful for two-person calls.

## Fully local/offline batch transcription

After the first run has successfully cached the models, put files in `~/Desktop/Input`, activate the virtual environment, and run:

```bash
source ~/.venvs/whisperx/bin/activate
python tools/transcribe_desktop_batch.py --offline --device cpu --compute-type int8
```

With `--offline`, the script sets offline model-cache environment variables before invoking WhisperX. It will not attempt to download missing models, so if a model is not already cached, the run will fail and you will need to do another online warm-up run.

## Common options

```bash
# Extract any ZIP files in Desktop/Input before transcribing.
python tools/transcribe_desktop_batch.py --offline --unzip --device cpu --compute-type int8

# Allow one to four speakers.
python tools/transcribe_desktop_batch.py --offline --min-speakers 1 --max-speakers 4 --device cpu --compute-type int8

# Use custom folders.
python tools/transcribe_desktop_batch.py --offline --input-dir /path/to/Input --output-dir /path/to/Output --device cpu --compute-type int8
```

## Notes

- First-time diarization model access requires a valid Hugging Face token and acceptance of the required model terms.
- Fully offline mode works only after WhisperX, Whisper, and diarization model files are already installed/cached locally.
- WhisperX writes text transcripts into `~/Desktop/Output` by default.
- Keep original media files in `Desktop/Input`; the script does not delete input or output files.
