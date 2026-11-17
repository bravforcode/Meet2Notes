# Windows audio capture diagnostic

Uses the existing Meet2Notes `WindowsWasapiCaptureBackend`, with one backend
per input so microphone and playback are saved as separate WAV files.
It is a standalone diagnostic; Meet2Notes continues to use its own mixed capture.

From the repository root, use an isolated environment (Python 3.12 on Windows):

```powershell
py -3.12 -m venv poc_audio/.venv
poc_audio/.venv/Scripts/python -m pip install PyAudioWPatch==0.2.12.8
poc_audio/.venv/Scripts/python poc_audio/dual_capture.py devices
```

Check the list and choose the microphone and system loopback that are actually
used by LINE, Zoom or Meet. IDs can change after a device is added or removed.
Once participants agree to recording, start a bounded capture explicitly:

```powershell
poc_audio/.venv/Scripts/python poc_audio/dual_capture.py record --seconds 30 --mic-id pyaudio:12 --system-id pyaudio:13 --output C:/temp/meeting-test-01
```

Replace IDs with the current ones. Output directory must not exist. This writes
`microphone.wav`, `system.wav`, and `capture.json`; listen to both files to
confirm each side. With speakers, microphone bleed may capture remote sound;
headphones usually make the test easier to interpret. Never publish recordings.
The backend streams start independently and can drift; WAVs are not sample
synchronized. On a capture or cleanup error, the tool attempts to close both
streams, records the errors in `capture.json`, and exits with failure. The
emergency release uses private upstream backend members and should be reviewed
when updating Meet2Notes. The recorded start time brackets are diagnostic only, not an
alignment guarantee. An output track can be silent if audio is routed elsewhere
or an application or OS does not expose it to loopback. Silence does not prove
that the meeting was captured. This tool does not join or control LINE/Meet/Zoom.

For a short hardware test without the microphone:

```powershell
poc_audio/.venv/Scripts/python poc_audio/dual_capture.py loopback-test --output C:/temp/loopback-test-01
```

It plays one second of low-volume 997 Hz tone to the default WASAPI output,
measures whether the same tone appears in its loopback, then deletes the WAV
because other system sounds could also have been captured. This may be audible.
The JSON measurement does not prove microphone capture or LINE compatibility.

Run the small automated tests:

```powershell
poc_audio/.venv/Scripts/python -m unittest discover -s poc_audio -p test_dual_capture.py
```
