# Thai speech smoke test — 17 November 2026

Source: [NECTEC LOTUSDIS](https://huggingface.co/datasets/nectec/LOTUSDIS), test split rows 0–4; CC BY-SA 4.0. Five short utterances; these do not represent LINE calls or Thai-English meetings. Dataset contamination in model training is unknown. Results do not establish a general model ranking.

| Engine / model | Device | Samples | Aggregate CER |
|---|---|---:|---:|
| openai-whisper 20250625 / tiny | CPU, PyTorch 2.12.1+cpu, fp32 | 5 | 45.89% |
| openai-whisper 20250625 / base | CPU, PyTorch 2.12.1+cpu, fp32 | first row only | 43.48% (10/23) |
| faster-whisper 1.2.1 / Systran faster-whisper-tiny revision d90ca5fe260221311c53c58e660288d3deb8d356 | CPU, int8, beam size 1 | first row only | 73.91% (17/23) |

The faster-whisper single-clip run used different decoding from the openai-whisper run, so the results are not a controlled comparison. On the first row alone openai-whisper tiny CER was 65.22% (15/23). CER uses NFC normalization and casefolding with whitespace and Unicode punctuation removed; numeric text normalization is not applied. Results are edit distance divided by reference characters, not percent of claims correct. No personal transcript is included in this report.

The tiny CPU run took 48.8–97.2 seconds per short clip while other work was running; these are observed wall times, not a controlled hardware benchmark. The installed PyTorch was CPU-only, so CUDA runs failed even though the machine has an RTX 2050. GPU performance is untested. The benchmark manifest and raw result JSON are intentionally ignored because future inputs may be private.

The base model's single clip took 54.317 seconds excluding its 11.697-second model load. Tiny and base used the same language and task settings; first-row CER was 65.22% and 43.48% respectively. One clip is far too small to establish the most accurate model. No LINE, real meeting call, diarization, or downstream summary quality was tested by this benchmark. See README for rerun instructions.
