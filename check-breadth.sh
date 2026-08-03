#!/usr/bin/env bash
# Progress of the breadth generation. Safe to run any time; read-only.
cd "$(dirname "$0")"
TARGET=36544   # records per model: mmath 8544 + belebele 21600 + global_mmlu 6400
printf '%-26s %-9s %8s %8s  %s\n' MODEL STATE DONE TARGET PCT
for M in qwen3_8b llama_3_1_8b_instruct; do
  PIDF=/tmp/breadth-$M.pid
  if [ -f "$PIDF" ] && kill -0 "$(cat $PIDF)" 2>/dev/null; then STATE=RUNNING; else STATE=EXITED; fi
  N=$(find "runs-breadth/$M" -name shard.jsonl 2>/dev/null -exec cat {} + | wc -l)
  printf '%-26s %-9s %8s %8s  %s%%\n' "$M" "$STATE" "$N" "$TARGET" "$((100*N/TARGET))"
done
echo
echo "per-cell:"
find runs-breadth -name shard.jsonl 2>/dev/null | sort | while read -r f; do
  printf '  %7s  %s\n' "$(wc -l < "$f" | tr -d ' ')" "${f#runs-breadth/}"
done
