#!/usr/bin/env bash
# Retry generation until the ledgers are complete. Safe: shards are append-only
# and generate_shard skips records that already exist, so a retry resumes.
cd "$(dirname "$0")"
for attempt in $(seq 1 40); do
  .venv/bin/python scripts/run_breadth_full.py --model qwen3_8b >>/tmp/breadth-qwen-retry.log 2>&1 && \
  .venv/bin/python - <<'PY' >>/tmp/sw4096-retry.log 2>&1
import sys; sys.path.insert(0,'.')
from pathlib import Path
import yaml
from src.benchmark_spec import load_spec
from src.engine import VLLMEngine
from src.run_breadth import run_cell
cfg = yaml.safe_load(Path("configs/models.yaml").read_text())
eng = VLLMEngine(str(cfg["models"]["qwen3_8b"]["endpoint"]), temperature=0.6, enable_thinking=False)
r = run_cell(eng, "qwen3_8b", load_spec("belebele"), "sw", Path("runs-breadth-sw4096"),
             base_seed=20260802, samples_per_item=8, max_tokens=4096)
print("belebele sw @4096 written", r.written)
PY
  N=$(find runs-breadth/qwen3_8b -name shard.jsonl -exec cat {} + | wc -l)
  S=$(wc -l < runs-breadth-sw4096/qwen3_8b/belebele/sw/native/shard.jsonl 2>/dev/null || echo 0)
  echo "$(date -Is) attempt $attempt: qwen=$N/36544 sw4096=$S/7200" >>/tmp/retry-progress.log
  [ "$N" -ge 36544 ] && [ "$S" -ge 7200 ] && { echo "COMPLETE" >>/tmp/retry-progress.log; exit 0; }
  sleep 10
done
