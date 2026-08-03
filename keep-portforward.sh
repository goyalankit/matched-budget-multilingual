#!/usr/bin/env bash
# Keep a vLLM port-forward alive. kubectl port-forward drops on network blips
# ("error: lost connection to pod"); this restarts it. Read-only w.r.t. the repo.
# Usage: ./keep-portforward.sh <local_port> <pod> [namespace]
PORT=${1:?port}; POD=${2:?pod}; NS=${3:-kingkong-dev}
while true; do
  kubectl port-forward "$POD" "${PORT}:8000" -n "$NS" >>"/tmp/pf${PORT}.log" 2>&1
  echo "$(date -Is) port-forward $PORT exited, restarting" >>"/tmp/pf${PORT}.log"
  sleep 3
done
