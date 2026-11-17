# Thai ASR smoke comparison

Run only on audio you are allowed to process. Public sample: [NECTEC LOTUSDIS](https://huggingface.co/datasets/nectec/LOTUSDIS), CC-BY-SA 4.0. It contains Thai far-field meetings. A few first rows are a smoke test, not a representative benchmark for a LINE call or code-switching. Some models may have trained on this dataset. Do not infer model rankings for other environments.

Requires Python, ffmpeg on PATH, and `openai-whisper` plus PyTorch. `--device cuda` requires a compatible PyTorch/CUDA installation. The chosen models are downloaded by Whisper if missing; check disk, memory and model licenses first. No cloud inference is used.

```powershell
python poc_benchmark/fetch_lotusdis.py --count 5 --out poc_benchmark/lotusdis
python poc_benchmark/benchmark.py --manifest poc_benchmark/lotusdis/manifest.json --models tiny base --device cpu --out poc_benchmark/results.json
```

A custom manifest is a UTF-8 JSON list of objects `{"audio":"relative.wav", "reference":"ถอดเสียงที่คนตรวจแล้ว"}`. Paths resolve relative to the manifest. The result contains transcripts: treat as sensitive, do not publish private data. CER is a character-level metric, not percent correctness, and punctuation/spacing are excluded after NFC and case folding. Compare names, English words, speakers, overlap, omissions, latency and human review separately. The report records errors per model rather than presenting failed runs as scores.
