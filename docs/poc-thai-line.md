# Thai-English meeting and Windows LINE proof of concept

This PoC extends Meet2Notes with an optional **Detailed Thai-English Meeting** note format, a Windows separate-track audio diagnostic and a small Thai ASR benchmark. The application itself uses the existing combined capture; the separate-track diagnostic is not integrated into the application pipeline.

## Start and use

1. Follow the upstream installation guide and install the capture and transcription extras. Use only models and providers whose terms you accept.
2. Start Meet2Notes on localhost. Select a microphone and the system output used by LINE, Zoom, Teams or Meet. Ask participants before recording.
3. Select the **Detailed Thai-English Meeting** note format. A separately installed local summary model or an explicitly configured provider is required. No local summary model was validated in this PoC.
4. Keep the original recording. Review every name, number, decision, owner, deadline and timestamp; the model may invent or omit information. Timestamps are prompt instructions, not verified source links.

For separate-track diagnostics, device selection and troubleshooting see [poc_audio/README.md](../poc_audio/README.md). Its two streams start independently and may drift; they are not sample-synchronized. The diagnostic does not join LINE or any meeting.

For dataset sourcing, model comparison, limitations and reproducible commands see [poc_benchmark/README.md](../poc_benchmark/README.md) and [poc_benchmark/RESULTS.md](../poc_benchmark/RESULTS.md). Do not upload private recordings or raw benchmark outputs to a public repository.

## Validation performed on 17 November 2026

- Upstream commit: b75077e588f5623d48d9c9bac05aa428b4257c52.
- Windows local app: home, settings and API documentation responded HTTP 200. Audio source discovery returned microphone and WASAPI loopback devices after installing PyAudioWPatch in the test environment.
- Native WASAPI loopback captured a generated 997 Hz tone. This did not test microphone input, LINE or a remote participant.
- The app imported a public LOTUSDIS test WAV, normalized it and completed a Faster Whisper tiny CPU transcription job with one segment. This is a pipeline smoke test, not a measure of transcript quality.
- Focused automated tests: five passed, one upstream dependency deprecation warning. They do not validate generated summary accuracy or real call capture.
- Five LOTUSDIS clips: OpenAI Whisper tiny corpus CER 45.89%. For row 0, tiny CER was 65.22% and base CER 43.48%; one clip is insufficient for model ranking. Details and decoder limitations are in the benchmark report.

## Next validation

1. With participant permission, record a Windows LINE test call with headphones and check both independently saved tracks, routing, clipping, drift and a longer call; repeat for Meet and Zoom.
2. Build a representative, permissioned Thai-English reference set with multiple microphones, speakers, terms, numbers, overlaps and call qualities. Benchmark ASR with identical inputs and record model revisions, latency and CER alongside name/number recall.
3. Test summary quality with a configured model and human-reviewed references. Check omissions, unsupported claims, incorrect owners/deadlines and whether evidence points to the correct time.
4. Audit privacy, dependencies, licenses, reliability, packaging and operational safeguards before using the PoC for real or sensitive meetings.
