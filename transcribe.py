#!/usr/bin/env python3
"""
Record until silence (or max_duration) and transcribe via Whisper.

Dependencies:
    pip install sounddevice soundfile webrtcvad openai

Requirements:
    - PortAudio (for sounddevice): e.g. on Ubuntu `sudo apt-get install portaudio19-dev`
    - Set your environment variable:
        export OPENAI_API_KEY="your_api_key_here"
"""

import os
import argparse
import collections
import time

import sounddevice as sd
import soundfile as sf
import webrtcvad
import numpy as np
import openai


def record_until_silence(
    filename: str,
    fs: int = 16000,
    aggression: int = 2,
    silence_limit: float = 1.0,
    max_duration: float = 10.0,
):
    """
    Record from mic until `silence_limit` seconds of silence have passed,
    or until `max_duration` is reached. Write to `filename`.
    """
    vad = webrtcvad.Vad(aggression)
    frame_ms = 30  # how long each frame is (in ms)
    frame_size = int(fs * frame_ms / 1000)  # samples per frame
    bytes_per_frame = frame_size * 2  # int16 → 2 bytes

    silence_frames = int(silence_limit * 1000 / frame_ms)
    max_frames = int(max_duration * 1000 / frame_ms)

    ring_buffer = collections.deque(maxlen=silence_frames)
    recorded_frames = []

    print(f"→ Listening (max {max_duration:.1f}s, stop after {silence_limit:.1f}s silence)...")
    with sd.RawInputStream(samplerate=fs, blocksize=frame_size,
                           dtype='int16', channels=1) as stream:
        for i in range(max_frames):
            data, _ = stream.read(frame_size)
            if len(data) < bytes_per_frame:
                break

            is_speech = vad.is_speech(data, fs)
            ring_buffer.append(is_speech)
            recorded_frames.append(data)

            # if our ring buffer is full of "False" → silence for long enough
            if len(ring_buffer) == silence_frames and not any(ring_buffer):
                print("✓ Detected silence, stopping early.")
                break

    # flatten and save
    audio = b"".join(recorded_frames)
    np_data = np.frombuffer(audio, dtype=np.int16)
    sf.write(filename, np_data, fs)
    print(f"✓ Saved to {filename} (duration: {len(np_data)/fs:.2f}s)")
    return filename


def transcribe_audio(path: str, model: str = "whisper-1") -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in your environment")
    openai.api_key = key

    with open(path, "rb") as f:
        result = openai.Audio.transcribe(model=model, file=f)
    return result["text"]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", default="out.wav",
                   help="where to save the recording")
    p.add_argument("--fs", type=int, default=16000, help="sampling rate")
    p.add_argument("--aggression", type=int, choices=[0,1,2,3], default=2,
                   help="webrtcvad aggressiveness (0–3)")
    p.add_argument("--silence", type=float, default=1.0,
                   help="seconds of silence to auto-stop")
    p.add_argument("--max", type=float, default=10.0,
                   help="maximum recording seconds")
    args = p.parse_args()

    wav = record_until_silence(
        filename=args.output,
        fs=args.fs,
        aggression=args.aggression,
        silence_limit=args.silence,
        max_duration=args.max,
    )

    print("→ Transcribing…")
    text = transcribe_audio(wav)
    print("\n=== Transcription ===")
    print(text)


if __name__ == "__main__":
    main()
