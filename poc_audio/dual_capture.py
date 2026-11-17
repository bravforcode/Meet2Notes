"""Opt-in Windows WASAPI diagnostic using the Meet2Notes capture backend.

Capture creates separate WAVs; they are not guaranteed to be sample-synchronized.
No device is opened until the user explicitly runs record or loopback-test.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import time
import wave
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from local_meeting_ai.adapters.audio_capture.windows_wasapi import WindowsWasapiCaptureBackend


def tone(rate: int, channels: int, seconds: float, frequency: float = 997) -> bytes:
    """Low-level synthetic signal for loopback diagnostics, signed 16-bit PCM."""
    samples = bytearray()
    for n in range(round(rate * seconds)):
        value = int(32767 * 0.03 * math.sin(2 * math.pi * frequency * n / rate))
        samples.extend(struct.pack("<h", value) * channels)
    return bytes(samples)


def tone_amplitude(path: Path, frequency: float = 997) -> dict[str, float]:
    with wave.open(str(path), "rb") as reader:
        rate, channels = reader.getframerate(), reader.getnchannels()
        if reader.getsampwidth() != 2:
            raise ValueError("Expected 16-bit PCM")
        raw = reader.readframes(reader.getnframes())
    samples = struct.iter_unpack("<h", raw)
    mono = [sample[0] / 32768 for i, sample in enumerate(samples) if i % channels == 0]
    if not mono:
        return {"seconds": 0, "amplitude": 0, "peak": 0}
    real = sum(x * math.cos(2 * math.pi * frequency * n / rate) for n, x in enumerate(mono))
    imag = sum(x * math.sin(2 * math.pi * frequency * n / rate) for n, x in enumerate(mono))
    return {"seconds": len(mono) / rate, "amplitude": 2 * math.hypot(real, imag) / len(mono),
            "peak": max(abs(x) for x in mono)}


def select(sources, kind, selected):
    candidates = [s for s in sources if (s.kind == "system") == (kind == "system")]
    if selected:
        candidates = [s for s in candidates if s.id == selected]
    if not candidates:
        raise RuntimeError(f"No {kind} input found; use 'devices' to inspect available inputs")
    return next((s for s in candidates if s.is_default and "wasapi" in s.host_api.casefold()),
                next((s for s in candidates if "wasapi" in s.host_api.casefold()),
                     next((s for s in candidates if s.is_default), candidates[0])))


def devices():
    sources = WindowsWasapiCaptureBackend().list_sources()
    for source in sources:
        print(json.dumps({"id": source.id, "name": source.name, "kind": source.kind,
                          "host_api": source.host_api, "sample_rate": source.sample_rate,
                          "channels": source.channels, "default": source.is_default}, ensure_ascii=False))
    return sources


def _emergency_close(backend):
    """Release each WASAPI resource independently if the upstream stop fails."""
    errors = []
    stream = getattr(backend, "_stream", None)
    writer = getattr(backend, "_wave", None)
    manager = getattr(backend, "_manager", None)
    for label, resource, method in (
        ("stream.stop_stream", stream, "stop_stream"),
        ("stream.close", stream, "close"),
        ("wave.close", writer, "close"),
        ("manager.terminate", manager, "terminate"),
    ):
        if resource is None:
            continue
        try:
            getattr(resource, method)()
        except BaseException as error:
            errors.append(f"{label}: {type(error).__name__}: {error}")
    try:
        backend._clear_unlocked()
    except BaseException as error:
        errors.append(f"clear state: {type(error).__name__}: {error}")
    return errors


def record(directory: Path, duration: float, mic_id: str | None, system_id: str | None):
    if not 0 < duration <= 3600:
        raise ValueError("Duration must be > 0 and <= 3600 seconds")
    directory.mkdir(parents=True, exist_ok=False)
    sources = WindowsWasapiCaptureBackend().list_sources()
    chosen = [select(sources, "microphone", mic_id), select(sources, "system", system_id)]
    backends = [WindowsWasapiCaptureBackend(), WindowsWasapiCaptureBackend()]
    started = []
    timings = {}
    primary_error = None
    cleanup_errors = []
    try:
        for source, backend, name in zip(chosen, backends, ("microphone", "system")):
            before = time.monotonic_ns()
            backend.start(session_id=str(uuid4()), source_id=source.id, destination=directory / f"{name}.wav")
            timings[name] = {"start_before_ns": before, "start_after_ns": time.monotonic_ns(),
                             "source_id": source.id, "source_name": source.name}
            started.append((name, backend))
        time.sleep(duration)
    except BaseException as error:
        primary_error = error
    finally:
        for name, backend in reversed(started):
            try:
                backend.stop()
            except BaseException as error:
                cleanup_errors.append(f"{name}: {type(error).__name__}: {error}")
                cleanup_errors.extend(f"{name}: emergency {detail}" for detail in _emergency_close(backend))
        metadata = {"streams": timings, "requested_seconds": duration,
            "status": "failed" if primary_error or cleanup_errors else "completed",
            "error": f"{type(primary_error).__name__}: {primary_error}" if primary_error else None,
            "cleanup_errors": cleanup_errors,
            "synchronization": "independent streams; timing offsets and drift are not corrected"}
        try:
            (directory / "capture.json").write_text(json.dumps(metadata,
                indent=2, ensure_ascii=False), encoding="utf-8")
        except BaseException as error:
            cleanup_errors.append(f"metadata: {type(error).__name__}: {error}")
    if primary_error:
        if cleanup_errors:
            primary_error.add_note("Cleanup failures: " + "; ".join(cleanup_errors))
        raise primary_error
    if cleanup_errors:
        raise RuntimeError("Recording cleanup failed: " + "; ".join(cleanup_errors))
    print(f"Captured {len(started)} streams in {directory}; inspect both WAV files.")


def loopback_test(directory: Path, system_id: str | None):
    """Play a synthetic tone and verify it is present on selected loopback; no microphone."""
    import pyaudiowpatch as pa
    directory.mkdir(parents=True, exist_ok=False)
    backend = WindowsWasapiCaptureBackend()
    source = select(backend.list_sources(), "system", system_id)
    manager = pa.PyAudio()
    stream = None
    started = False
    try:
        output = manager.get_default_wasapi_device(d_out=True)
        # A selected loopback other than the Windows default is intentionally not claimed as tested.
        default_loopback = manager.get_default_wasapi_loopback()
        if int(source.id.split(":")[1]) != int(default_loopback["index"]):
            raise RuntimeError("Loopback test plays on the default output; select its loopback")
        rate = int(output["defaultSampleRate"])
        channels = min(2, int(output["maxOutputChannels"]))
        stream = manager.open(format=pa.paInt16, channels=channels, rate=rate,
                              output=True, output_device_index=output["index"])
        path = directory / "loopback.wav"
        backend.start(session_id=str(uuid4()), source_id=source.id, destination=path)
        started = True
        time.sleep(0.3)
        stream.write(tone(rate, channels, 1.0))
        time.sleep(0.3)
    finally:
        if started:
            backend.stop()
        if stream is not None:
            stream.close()
        manager.terminate()
    try:
        result = tone_amplitude(path)
    finally:
        # The loopback may contain other system audio. Keep measurements, not the recording.
        path.unlink(missing_ok=True)
    result.update({"frequency_hz": 997, "loopback_source": source.name,
                   "passed": result["seconds"] > 0.5 and result["amplitude"] > 0.001,
                   "scope": "synthetic system output only; not a LINE call or microphone test"})
    (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("devices")
    rec = sub.add_parser("record", help="record microphone and system audio into separate WAVs")
    rec.add_argument("--output", type=Path, required=True)
    rec.add_argument("--seconds", type=float, required=True)
    rec.add_argument("--mic-id")
    rec.add_argument("--system-id")
    test = sub.add_parser("loopback-test", help="play and capture a short synthetic tone; no microphone")
    test.add_argument("--output", type=Path, required=True)
    test.add_argument("--system-id")
    args = parser.parse_args()
    if args.command == "devices":
        devices()
    elif args.command == "record":
        record(args.output, args.seconds, args.mic_id, args.system_id)
    else:
        loopback_test(args.output, args.system_id)


if __name__ == "__main__":
    main()
