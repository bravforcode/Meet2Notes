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

## Two simulated Thai-English speakers, 17 November 2026

We synthesized two fictional sentences using local Windows SAPI Microsoft
Pattara and Google Translate Thai TTS (only the fictional second sentence was
sent over the network). We injected them on separate simulated microphone and
remote input channels into Meet2Notes' actual `AudioMixer`, without opening any
microphone. Both source tracks survived in their designated time windows:
source-vs-mix signal correlation was 0.99999996 and 0.99999998. This is a
software-input check; it does not validate a microphone, device loopback, LINE,
overlap, diarization, or the accuracy of the generated spoken pronunciation.

OpenAI Whisper 20250625, PyTorch 2.12.1 CPU, FP32, language `th`, 4 OMP/MKL
threads; same generated recording for both models. CER normalizes Unicode NFC,
case and punctuation/whitespace, but not synonyms or number forms.

| Model | Per-turn CER, both sides combined | Full two-turn recording CER | Literal English terms | Literal day/time terms |
|---|---:|---:|---:|---:|
| tiny | 61.36% (27/44) | 54.55% (24/44) | 0/2 | 0/2 |
| base | 56.82% (25/44) | 79.55% (35/44) | 0/2 | 0/2 |

The full-recording base hypothesis included the first turn but omitted the
second in this run. Literal checks require the exact strings `report`, `email`,
`วันศุกร์`, and `บ่ายสามโมง`; Thai transliterations and equivalent meanings are
counted as misses. This metric does not establish semantic errors on its own.
The reference is the text supplied to each TTS engine, not an independently
human-audited transcript of what it actually pronounced. Two short synthesized
sentences cannot determine the best model or real-call accuracy. Total mixed WAV
SHA-256: `3a0a2459dad85911c2bab576cc162fe3b68eac56c5bb6477395925bee7185bd9`;
TTS output can vary when regenerated. This run's per-turn decoding took about
0.66–1.08 seconds per clip with models already loaded; the small fixture and
machine load make that unsuitable as a real-time performance claim.

Next candidates: benchmark [MERaLiON-3-3B-ASR](https://huggingface.co/MERaLiON/MERaLiON-3-3B-ASR)
and larger Whisper variants under the same fixed dataset and device budget after
checking model terms and available memory. Neither candidate was run here.
