import tempfile
import unittest
import wave
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dual_capture import record, select, tone, tone_amplitude


class AudioTests(unittest.TestCase):
    def test_generated_tone_has_expected_amplitude(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tone.wav"
            with wave.open(str(path), "wb") as out:
                out.setnchannels(2)
                out.setsampwidth(2)
                out.setframerate(48000)
                out.writeframes(tone(48000, 2, 1))
            measured = tone_amplitude(path)
            self.assertAlmostEqual(measured["seconds"], 1.0)
            self.assertAlmostEqual(measured["amplitude"], 0.03, places=3)

    def test_select_rejects_missing_device(self):
        with self.assertRaisesRegex(RuntimeError, "No system input"):
            select([], "system", None)

    def test_stop_failure_closes_resources_and_other_stream_and_records_error(self):
        mic = SimpleNamespace(id="pyaudio:1", kind="microphone", name="mic",
                              host_api="Windows WASAPI", is_default=True)
        system = SimpleNamespace(id="pyaudio:2", kind="system", name="output",
                                 host_api="Windows WASAPI", is_default=True)
        discovery = Mock()
        discovery.list_sources.return_value = [mic, system]
        mic_backend = Mock()
        system_backend = Mock()
        system_backend.stop.side_effect = RuntimeError("driver failed")
        system_backend._stream = Mock()
        system_backend._wave = Mock()
        system_backend._manager = Mock()
        system_backend._clear_unlocked = Mock()
        with tempfile.TemporaryDirectory() as tmp, \
             patch("dual_capture.WindowsWasapiCaptureBackend",
                   side_effect=[discovery, mic_backend, system_backend]), \
             patch("dual_capture.time.sleep"):
            output = Path(tmp) / "recording"
            with self.assertRaisesRegex(RuntimeError, "driver failed"):
                record(output, 1, None, None)
            metadata = json.loads((output / "capture.json").read_text(encoding="utf-8"))
        mic_backend.stop.assert_called_once()
        system_backend._stream.stop_stream.assert_called_once()
        system_backend._stream.close.assert_called_once()
        system_backend._wave.close.assert_called_once()
        system_backend._manager.terminate.assert_called_once()
        system_backend._clear_unlocked.assert_called_once()
        self.assertEqual(metadata["status"], "failed")
        self.assertIn("driver failed", metadata["cleanup_errors"][0])

    def test_capture_failure_stops_both_streams_and_records_primary_error(self):
        mic = SimpleNamespace(id="pyaudio:1", kind="microphone", name="mic",
                              host_api="Windows WASAPI", is_default=True)
        system = SimpleNamespace(id="pyaudio:2", kind="system", name="output",
                                 host_api="Windows WASAPI", is_default=True)
        discovery, first, second = Mock(), Mock(), Mock()
        discovery.list_sources.return_value = [mic, system]
        with tempfile.TemporaryDirectory() as tmp, \
             patch("dual_capture.WindowsWasapiCaptureBackend", side_effect=[discovery, first, second]), \
             patch("dual_capture.time.sleep", side_effect=RuntimeError("capture interrupted")):
            output = Path(tmp) / "recording"
            with self.assertRaisesRegex(RuntimeError, "capture interrupted"):
                record(output, 1, None, None)
            metadata = json.loads((output / "capture.json").read_text(encoding="utf-8"))
        first.stop.assert_called_once()
        second.stop.assert_called_once()
        self.assertEqual(metadata["status"], "failed")
        self.assertIn("capture interrupted", metadata["error"])


if __name__ == "__main__":
    unittest.main()
