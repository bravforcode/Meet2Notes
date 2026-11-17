"""Generate a two-speaker Thai/English synthetic meeting fixture.

Only fictional text is sent to Google Translate TTS. No microphone is opened.
The software mixer is the same mixer used by Meet2Notes combined capture, but
input packets are simulated and this does not test physical microphone capture.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from local_meeting_ai.adapters.audio_capture.mixer import AudioMixer
from local_meeting_ai.domain.entities import AudioCaptureSource

RATE = 48000
TURNS = [
    {
        "speaker": "mic_simulated",
        "voice": "Microsoft Pattara (local SAPI)",
        "reference": "ส่ง report วันศุกร์นะ",
        "expected_terms": ["report", "วันศุกร์"],
    },
    {
        "speaker": "remote_simulated",
        "voice": "Google Translate Thai (network TTS)",
        "reference": "รับทราบ ส่ง email บ่ายสามโมง",
        "expected_terms": ["email", "บ่ายสามโมง"],
    },
]


def create_turn(turn: dict, output: Path) -> np.ndarray:
    wav = output / (turn["speaker"] + ".wav")
    if turn["speaker"] == "mic_simulated":
        source = output / "sapi-source.wav"
        def escaped(s):
            return str(s).replace("'", "''")

        script = (
            "$ErrorActionPreference = 'Stop'; Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.SelectVoice('Microsoft Pattara'); "
            f"$s.SetOutputToWaveFile('{escaped(source.resolve())}'); "
            f"$s.Speak('{escaped(turn['reference'])}'); $s.Dispose()"
        )
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], check=True
        )
    else:
        source = output / "google-source.mp3"
        query = urllib.parse.urlencode(
            {"ie": "UTF-8", "tl": "th", "client": "tw-ob", "q": turn["reference"]}
        )
        request = urllib.request.Request(
            "https://translate.google.com/translate_tts?" + query,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            source.write_bytes(response.read())
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ar",
            str(RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
    )
    with wave.open(str(wav), "rb") as source:
        return np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").copy()


def wav_write(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm)


def mix_tracks(
    samples: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[int, int]]]:
    gap = RATE // 2
    size = len(samples[0]) + gap + len(samples[1])
    track_a = np.zeros(size, dtype="<i2")
    track_b = np.zeros(size, dtype="<i2")
    track_a[: len(samples[0])] = samples[0]
    second_start = len(samples[0]) + gap
    track_b[second_start:] = samples[1]
    sources = [
        AudioCaptureSource(
            id=name,
            name=name,
            kind=kind,
            backend="synthetic",
            host_api="none",
            channels=1,
            sample_rate=RATE,
        )
        for name, kind in [("mic_simulated", "microphone"), ("remote_simulated", "system")]
    ]
    mixer = AudioMixer(sources)
    pieces = []
    for start in range(0, size, 4800):
        end = min(size, start + 4800)
        mixer.push(sources[0].id, track_a[start:end].tobytes(), start / RATE)
        mixer.push(sources[1].id, track_b[start:end].tobytes(), start / RATE)
        pieces.append(mixer.read(end - start))
    mixed = np.frombuffer(b"".join(pieces), dtype="<i2")
    regions = [(0, len(samples[0])), (second_start, size)]
    return mixed, track_a, track_b, regions


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    samples = [create_turn(turn, output) for turn in TURNS]
    mixed, track_a, track_b, regions = mix_tracks(samples)
    wav_write(output / "mixed.wav", mixed.tobytes())
    wav_write(output / "track-microphone-simulated.wav", track_a.tobytes())
    wav_write(output / "track-remote-simulated.wav", track_b.tobytes())
    manifest, verification = [], []
    for turn, (start, end), signal in zip(TURNS, regions, samples, strict=False):
        piece = mixed[start:end]
        output_name = turn["speaker"] + "-mixed.wav"
        wav_write(output / output_name, piece.tobytes())
        rms = float(np.sqrt(np.mean(piece.astype(np.float64) ** 2)))
        correlation = float(np.corrcoef(piece, signal)[0, 1]) if rms else 0.0
        verification.append(
            {
                "speaker": turn["speaker"],
                "rms": rms,
                "correlation": correlation,
                "nonzero": bool(np.any(piece)),
                "seconds": (end - start) / RATE,
            }
        )
        manifest.append(
            {
                "audio": output_name,
                "reference": turn["reference"],
                "speaker": turn["speaker"],
                "voice": turn["voice"],
                "expected_terms": turn["expected_terms"],
            }
        )
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    combined_manifest = [
        {
            "audio": "mixed.wav",
            "reference": " ".join(turn["reference"] for turn in TURNS),
            "expected_terms": [term for turn in TURNS for term in turn["expected_terms"]],
        }
    ]
    (output / "full-manifest.json").write_text(
        json.dumps(combined_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "mix-check.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    if not all(row["nonzero"] and row["correlation"] > 0.99 for row in verification):
        raise RuntimeError("Synthetic mixer failed to preserve both source signals")
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.output)
