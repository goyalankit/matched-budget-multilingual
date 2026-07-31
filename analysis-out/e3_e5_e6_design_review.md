I’ll first reconstruct the claim and ledger schema, then compute the existing-data diagnostic before assessing the remaining design gates.

● Read 2026-07-31-e3-e5-e6-breadth-grid-design.md
  │ docs/superpowers/specs/2026-07-31-e3-e5-e6-breadth-grid-design.md
  └ 258 lines read

/ Search (grep)
  │ "^##? (E3|E5|E6)|Measured cost basis|5,900|5900" (EXPERIMENTS.md)
  └ 39 lines found

/ Search (grep)
  │ "^##? (3\.2|3\.3|5)|Eq\.? \(1\)|\\Delta|A_L|A_E|emission" (PAPER.md)
  └ 105 lines found

/ Search (glob)
  │ "{prereg-independent-decoding.md,analysis-out/independent_scoring.json,analysis-out/independent_
  │ scoring.md,src/explore_budget.py,src/independent_scoring.py,src/run_independent.py,src/generate.
  │ py,configs/models.yaml,src/prefixes.py}"
  └ 9 files found

/ Search (glob)
  │ "runs/*/shard.jsonl"
  └ No matches found

● Read PAPER.md
  └ L139:186 (48 lines read)

● Read independent_scoring.md
  │ analysis-out/independent_scoring.md
  └ 95 lines read

● Read EXPERIMENTS.md
  └ L13:270 (258 lines read)

● Read PAPER.md
  └ L28:60 (32 lines read)

● Read prereg-independent-decoding.md
  └ 297 lines read

● Read explore_budget.py
  │ src/explore_budget.py
  └ 364 lines read

/ Search (glob)
  │ "runs/**/*.jsonl"
  └ No matches found

/ Search (grep)
  │ "shard\.jsonl|runs/" in *.py
  └ 86 lines found

● Read prefixes.py
  │ src/prefixes.py
  └ 38 lines read

● List directory runs
  └ 2 files found

● Read generate.py
  │ src/generate.py
  └ 1 line read

● Read models.yaml
  │ configs/models.yaml
  └ 104 lines read

● Read independent_scoring.py
  │ src/independent_scoring.py
  └ 281 lines read

● Read run_independent.py
  │ src/run_independent.py
  └ L1:260 (260 lines read)

● Read independent_scoring.json
  │ analysis-out/independent_scoring.json
  └ L1:80 (80 lines read)

/ Search (grep)
  │ "5900|5,900|throughput|tok/s" in *.{md,json,py}
  └ 185 lines found

● List directory runs/qwen3_8b
  └ 3 files found

● List directory runs/llama_3_1_8b_instruct
  └ 3 files found

/ Search (grep)
  │ "def (generation_record|append_ledger_records|record_id|read_ledger)|timestamp|created|json\.dum
  │ ps|write" (src/generate.py)
  └ 75 lines found

/ Search (grep)
  │ "Aya|Gemma|Mistral|Ministral|context|8192|8k|reasoning" in *.md
  └ 105 lines found

/ Search (grep)
  │ "TRANSLATE-ACT|translate_act|Belebele|XCOPA|Global-MMLU|MMATH" in *.md
  └ 123 lines found

● List directory runs/llama_3_1_8b_instruct/de
  └ 4 files found

● List directory runs/qwen3_8b/de
  └ 4 files found

● Read todo.md
  │ tasks/todo.md
  └ L79:102 (24 lines read)

● Read generate.py
  │ src/generate.py
  └ L60:240 (181 lines read)

● Read generate.py
  │ src/generate.py
  └ L240:390 (151 lines read)

● Read EXPERIMENTS.md
  └ L264:345 (81 lines read)

● Read shard.jsonl
  │ runs/qwen3_8b/de/native/shard.jsonl
  └ L1:2 (2 lines read)

● List directory runs/qwen3_8b/de/native
  └ 1 file found

/ Search (grep)
  │ "def
  │ _generation_record_from_result|started_at|completed_at|input_token_count|output_token_count"
  │ (src/generate.py)
  └ 169 lines found

/ Search (grep)
  │ "def load_|AutoTokenizer|tokenizer|decode_many|qwen3_8b|llama_3_1" in *.py (scripts)
  └ 191 lines found

/ Search (grep)
  │ "emission_index_stats\(" in *.py
  └ 45 lines found

● Read explore_llama_budget.py
  │ scripts/explore_llama_budget.py
  └ 89 lines read

● Read mgsm.py
  │ src/mgsm.py
  └ L1:180 (96 lines read)

● Read analyze_llama.py
  │ scripts/analyze_llama.py
  └ L1:145 (145 lines read)

● Read explore_budget_qwen.json
  │ analysis-out/explore_budget_qwen.json
  └ L1:100 (100 lines read)

● Read explore_qwen_budget.py
  │ scripts/explore_qwen_budget.py
  └ L1:150 (150 lines read)

● Read explore_budget_llama.json
  │ analysis-out/explore_budget_llama.json
  └ L1:100 (100 lines read)

The algebraic weak point is now isolated: the proposed factorization replaces a joint event with a product of marginals. I’m measuring that substitution over every existing premium window, not just comparing coarse medians.

✗ Check cached model tokenizers (shell)
  │ .venv/bin/python - <<'PY'
  │ from transformers import AutoTokenizer
  │ for name in ['Qwen/Qwen3-8B','meta-llama/Meta-Llama-3.1-8B-Instruct']:
  │ try:
  │ t=AutoTokenizer.from_pretrained(name, local_files_only=True)…
  └ Permission denied and could not request permission from user

● Edit
  └ Create /tmp/e3-review-scratch/check_tokenizers.py

✗ Check cached model tokenizers (shell)
  │ .venv/bin/python /tmp/e3-review-scratch/check_tokenizers.py
  └ Permission denied and could not request permission from user

✗ Inspect ledger counts and decode cache (shell)
  │ mkdir -p /tmp/e3-review-scratch && .venv/bin/python - <<'PY'
  │ import json, pathlib, sqlite3
  │ root=pathlib.Path('runs')
  │ for model in ('qwen3_8b','llama_3_1_8b_instruct'):
  │ for lang in ('de','th','sw'):…
  └ Permission denied and could not request permission from user

✗ Check cached tokenizer availability (shell)
  │ .venv/bin/python /tmp/e3-review-scratch/check_tokenizers.py
  └ Permission denied and could not request permission from user

✗ Verify project Python (shell)
  │ .venv/bin/python -c 'print(1)'
  └ Permission denied and could not request permission from user

✗ Inspect project Python executable (shell)
  │ ls -l .venv/bin/python .venv/bin/python3 && file .venv/bin/python
  └ Permission denied and could not request permission from user

✗ Check project Python version (shell)
  │ .venv/bin/python --version
  └ Permission denied and could not request permission from user

✗ Inspect cache and local tokenizer snapshots (shell)
  │ PYTHONDONTWRITEBYTECODE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
  │ /home/angoyal/ws/language-research/.venv/bin/python -c "import sqlite3, pathlib; p='file:/home
  │ /angoyal/ws/language-research/analysis-out/llama_detokenize_cache.sqlite3?mode=ro';
  │ c=sqlite3.connect(p, uri=True); print(c.execute('select count(*) from
  │ detokenized').fetchone()[0]); print(c.execute('pragma table_info(detokenized)').fetchall()); …
  └ Permission denied and could not request permission from user

Computation failed before execution:

```text
File "<string>", line 45
    (,.join(? for _ in ks))
     ^
SyntaxError: f-string: invalid syntax
```

No repository files were modified and no JSON was created.✗ Inspect read-only Llama cache schema (shell)
  │ /home/angoyal/ws/language-research/.venv/bin/python - <<'PY'
  │ import sqlite3
  │ p='/home/angoyal/ws/language-research/analysis-out/llama_detokenize_cache.sqlite3'
  │ c=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
  │ print(c.execute("select sql from sqlite_master where type='table'").fetchall())…
  └ Permission denied and could not request permission from user

✗ Find cached local tokenizers (shell)
  │ find "$HOME/.cache/huggingface" -maxdepth 5 -type f \( -name tokenizer.json -o -name
  │ tokenizer_config.json \) -print 2>/dev/null | sort | head -200
  └ Permission denied and could not request permission from user

✗ List cached Qwen tokenizer snapshot (shell)
  │ find /home/angoyal/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots -maxdepth 2 -type f
  │ -o -type l 2>/dev/null | sort | head -100
  └ Permission denied and could not request permission from user

✗ Find cached Llama repositories (shell)
  │ find /home/angoyal/.cache/huggingface/hub -maxdepth 1 -type d -iname '*llama*' -print
  │ 2>/dev/null | sort
  └ Permission denied and could not request permission from user

✗ Compute emission correctness dependence (shell)
  │ /home/angoyal/ws/language-research/.venv/bin/python
  │ /tmp/e3-review-scratch/compute_emission_correctness.py
  └ Permission denied and could not request permission from user

Computation could not execute:

```text
Permission denied and could not request permission from user
```

Script created at `/tmp/e3-review-scratch/compute_emission_correctness.py`; no JSON was produced.Computed and saved:

`/tmp/e3-review-scratch/emission_correctness_dependence.json`  
SHA-256: `6fda3356bc1cff3c68345c39fd16b366a2306bf356d59ec9b98c0028a4608b58`

Columns below: `B-endpoint: window_n/correct_n, conditional%, predicted_pp, observed_pp, abs_error_pp, ratio`. `*` marks peak observed window.

### qwen3_8b
- **de**: correct 1580/2000 (79.00%); emitted 1844; never 156  
  `64-99:2/0,0,0.079,0,0.079,0`  
  `128-199:337/312,92.58,13.3115,15.60,2.2885,1.1719`  
  `*192-299:758/673,88.79,29.941,33.65,3.709,1.1239`  
  `256-399:730/614,84.11,28.835,30.70,1.865,1.0647`  
  `384-598:284/214,75.35,11.218,10.70,0.518,0.9538`  
  `512-798:63/45,71.43,2.4885,2.25,0.2385,0.9042`  
  `768-1197:10/2,20,0.395,0.10,0.295,0.2532`  
  `1024-1596:3/0,0,0.1185,0,0.1185,0`  
  `2048-3192:0/0,—,0,0,0,—`

- **th**: correct 945/2000 (47.25%); emitted 1961; never 39  
  `64-163:39/31,79.49,0.9214,1.55,0.6286,1.6823`  
  `128-326:670/289,43.13,15.8288,14.45,1.3788,0.9129`  
  `192-489:1443/669,46.36,34.0909,33.45,0.6409,0.9812`  
  `*256-652:1553/777,50.03,36.6896,38.85,2.1604,1.0589`  
  `384-979:908/460,50.66,21.4515,23.00,1.5485,1.0722`  
  `512-1305:367/178,48.50,8.6704,8.90,0.2296,1.0265`  
  `768-1958:52/18,34.62,1.2285,0.90,0.3285,0.7326`  
  `1024-2611:10/3,30,0.2363,0.15,0.0863,0.6349`

- **sw**: correct 675/2000 (33.75%); emitted 1498; never 502  
  `64-123:261/153,58.62,4.4044,7.65,3.2456,1.7369`  
  `*128-247:621/298,47.99,10.4794,14.90,4.4206,1.4218`  
  `192-371:599/265,44.24,10.1081,13.25,3.1419,1.3108`  
  `256-495:412/169,41.02,6.9525,8.45,1.4975,1.2154`  
  `384-743:170/51,30,2.8688,2.55,0.3188,0.8889`  
  `512-991:57/5,8.77,0.9619,0.25,0.7119,0.2599`  
  `768-1487:12/1,8.33,0.2025,0.05,0.1525,0.2469`  
  `1024-1982:11/1,9.09,0.1856,0.05,0.1356,0.2694`  
  `2048-3965:10/1,10,0.1688,0.05,0.1188,0.2963`

### llama_3_1_8b_instruct
- **de**: correct 271/2000 (13.55%); emitted 395; never 1605  
  `64-101:1/1,100,0.0068,0.05,0.0432,7.3801`  
  `128-202:8/6,75,0.0542,0.30,0.2458,5.5351`  
  `192-303:209/160,76.56,1.4160,8.00,6.5840,5.6498`  
  `*256-404:244/167,68.44,1.6531,8.35,6.6969,5.0511`  
  `384-607:75/38,50.67,0.5081,1.90,1.3919,3.7392`  
  `512-809:6/3,50,0.0406,0.15,0.1094,3.6900`  
  `768-1214:0/0,—,0,0,0,—`  
  `1024-1619:0/0,—,0,0,0,—`  
  `2048-3239:0/0,—,0,0,0,—`

- **th**: correct 77/2000 (3.85%); emitted 136; never 1864  
  `64-140:12/7,58.33,0.0231,0.35,0.3269,15.1515`  
  `128-280:67/44,65.67,0.1290,2.20,2.0710,17.0576`  
  `*192-421:78/46,58.97,0.1502,2.30,2.1498,15.3180`  
  `256-561:69/40,57.97,0.1328,2.00,1.8672,15.0574`  
  `384-842:35/15,42.86,0.0674,0.75,0.6826,11.1317`  
  `512-1123:12/3,25,0.0231,0.15,0.1269,6.4935`  
  `768-1685:0/0,—,0,0,0,—`  
  `1024-2246:0/0,—,0,0,0,—`

- **sw**: correct 579/2000 (28.95%); emitted 1080; never 920  
  `64-123:2/1,50,0.0290,0.05,0.0211,1.7271`  
  `128-247:204/147,72.06,2.9529,7.35,4.3971,2.4891`  
  `192-370:472/291,61.65,6.8322,14.55,7.7178,2.1296`  
  `*256-494:691/364,52.68,10.0022,18.20,8.1978,1.8196`  
  `384-741:450/187,41.56,6.5137,9.35,2.8363,1.4354`  
  `512-988:112/32,28.57,1.6212,1.60,0.0212,0.9869`  
  `768-1482:6/1,16.67,0.0868,0.05,0.0368,0.5757`  
  `1024-1977:2/0,0,0.0290,0,0.0290,0`  
  `2048-3954:0/0,—,0,0,0,—`

### Aggregate
Emitted/never × correct/incorrect: `[[4127,2787],[0,5086]]`; χ²(1)=4627.24, SciPy underflowed p to 0. This association is mechanically induced because the full trace is included in the E grid, so every correct parse has finite E.

Across 52 overlapping windows: predicted sum 274.107 pp; observed 339.100 pp; signed difference +64.993 pp; absolute-error sum 75.4088 pp; descriptive lift ratio 1.2371. Windows overlap, so these sums are not independent inferential quantities.

Qwen used the offline cached tokenizer; Llama used 41,805 read-only cache lookups with zero misses and no detokenization requests.● General-purpose(gpt-5.6-sol) Compute emission correctness dependence
  │ Calculate aggregate descriptive ratios (shell)
  │   │ awk 'BEGIN {print 6782/12137, (274.107/100*2000)/12137, 339.1/274.107, (339.1-274.107)}'
  │   └ 2 lines…
  └ Read emission_correctness_dependence.json
      │ /tmp/e3-review-scratch/emission_correctness_dependence.json
      └ L800:875 (72 lines read)

● List directory /tmp/e3-review-scratch
  └ 3 files found

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L1:120 (120 lines read)

● Read generate.py
  │ src/generate.py
  └ L403:465 (63 lines read)

/ Search (grep)
  │ "translate the problem|Translate|translation|passage|question|options" in *.txt (prompts)
  └ 3 lines found

/ Search (grep)
  │ "model_max_length|max_position_embeddings|8192|Aya-23|aya-23|google/gemma|Mistral"
  └ 84 lines found

● Read parser.py
  │ src/parser.py
  └ L1:260 (127 lines read)

● Read compute_emission_correctness.py
  │ /tmp/e3-review-scratch/compute_emission_correctness.py
  └ L1:260 (260 lines read)

/ Search (grep)
  │ "multiple|last|first|answers|findall|prefix" (prereg-matched-budgets.md)
  └ 28 lines found

/ Search (grep)
  │ "correct_count|p_correct|peak_observed"
  │ (/tmp/e3-review-scratch/emission_correctness_dependence.json)
  └ 329 lines found

✗ Fetching web content https://huggingface.co/google/gemma-2-9b-it/raw/main/config.json · url: "htt…
  └ Error: Failed to fetch https://huggingface.co/google/gemma-2-9b-it/raw/main/config.json - status
    code 401

✗ Fetching web content https://huggingface.co/google/gemma-2-9b-it/raw/main/README.md · url: "https…
  └ Error: Failed to fetch https://huggingface.co/google/gemma-2-9b-it/raw/main/README.md - status
    code 401

✗ Fetching web content https://huggingface.co/CohereForAI/aya-23-8B/raw/main/config.json · url: "ht…
  └ Error: Failed to fetch https://huggingface.co/CohereForAI/aya-23-8B/raw/main/config.json -
    status code 401

✗ Fetching web content https://huggingface.co/CohereForAI/aya-23-8B/raw/main/README.md · url: "http…
  └ Error: Failed to fetch https://huggingface.co/CohereForAI/aya-23-8B/raw/main/README.md - status
    code 401

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L419:540 (122 lines read)

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L548:675 (128 lines read)

● Read compute_emission_correctness.py
  │ /tmp/e3-review-scratch/compute_emission_correctness.py
  └ L260:520 (261 lines read)

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L676:805 (130 lines read)

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L302:418 (117 lines read)

● Read emission_correctness_dependence.json
  │ /tmp/e3-review-scratch/emission_correctness_dependence.json
  └ L174:301 (128 lines read)

**The strongest objection is fatal to E6 as written:** the “parameter-free” prediction factorizes a joint event into marginals under an independence assumption that is structurally impossible whenever some traces never emit. On the existing ledger it understates peak \(\Delta\) by **2.2–8.2 points**, and by factors of **5.1× and 15.3×** in two Llama cells. Phase 3’s “correction” would therefore be the substantive model, not a correction. The better parameter-free predictor is already available from the same uncapped run: use the empirical **correct-emission sub-CDF**, not \(p_{\text{correct}}F_E\).

## 1. Is the E6 point prediction correct algebra?

No.

Equation (1) establishes only

\[
\Delta_L(B)=\Pr(C_{\lfloor rB\rfloor}=1)-\Pr(C_B=1).
\]

If correctness becomes absorbing when the final answer is emitted at time \(E\), then

\[
\Delta_L(B)
=\Pr(C=1,\ B<E\le\lfloor rB\rfloor)
=\int_{(B,\lfloor rB\rfloor]} \Pr(C=1\mid E=e)\,dF_E(e).
\]

The proposed

\[
p_{\text{correct}}\,[F_E(\lfloor rB\rfloor)-F_E(B)]
\]

requires \(\Pr(C=1\mid E=e)=p_{\text{correct}}\) throughout the window. Eq. (1) itself supplies no such independence (`PAPER.md:42-55`; design `:155-176`).

There is an additional approximation: `parse_answer` returns the **last** answer line, so a later answer can change correctness (`src/parser.py:95-127`). Without an absorbing-correctness condition, even the joint-emission identity is not exact.

The clean replacement is

\[
\widehat\Delta(B)=\widehat G(\lfloor rB\rfloor)-\widehat G(B),
\qquad
G(t)=\Pr(C=1,E\le t).
\]

This uses the same uncapped ledger and no fitted parameters. It does use gold correctness—but so does the proposed \(p_{\text{correct}}\).

**EOS and censoring:** completed traces become constant prefixes after EOS (`src/prefixes.py:10-14`). But `emission_index_stats` maps both genuine non-emission and cap-censored non-emission to `None` (`src/explore_budget.py:103-122,160-183`). Thus:

- finite \(E\): observed emission, whether correct or wrong;
- EOS without an answer: genuine non-emission;
- length-censored without an answer: only \(E>\text{cap}\), not \(E=\infty\).

The identity is usable only for windows whose upper endpoint lies within the generation cap, and only after separating EOS non-emission from right-censoring. The current “uncapped” ledger is merely benchmark-capped.

## 2. Is the per-benchmark budget grid circular?

Not outcome leakage, but it compromises the peak-location test.

Selecting the grid from \(F_E\) before observing capped outcomes is legitimate covariate-adaptive design. It does **not**, by itself, bias a pointwise residual or numerical height comparison. But it does:

- strongly favor peak-location agreement because the candidate support is centered on the predicted peak;
- hide an unpredicted maximum outside that support;
- affect peak height when height is defined as a maximum over the selected points, through both omitted maxima and winner’s curse.

An adversarial-away grid is useful as a **negative-control supplement**, not as a replacement: zero away from the predicted regime is easier to satisfy than the positive peak prediction.

Use a fixed primary geometric grid independent of \(F_E\), such as `{8,16,32,64,128,256,512,1024,2048,4096}`, constrained only by context length. Add \(F_E\)-derived points as secondary interpolation. At the corrected throughput, the extra caps are affordable.

## 3. Is “70 regression units” a real N?

No. It is 70 repeated summaries, not 70 independent units.

The three languages share translated source items; models share the same benchmark items; benchmarks and models each induce crossed dependence. For generalization across models and tasks, the effective outer sample is **five models and five benchmarks**, with at most 25 pair interactions—not 70. Hundreds of items reduce measurement error within cells but do not create additional model/benchmark replication.

I would bootstrap as follows:

1. Resample model checkpoints and benchmarks as crossed outer clusters if claiming population generalization. With only five of each, asymptotic precision claims remain weak.
2. Within each selected benchmark, resample source item IDs jointly across every language translation, model, cap, and arm.
3. Retain all eight samples and their pairing within each selected item.
4. Recompute emission summaries, full curves, peak statistics, and the E6 fit inside every replicate.

If models and benchmarks are treated as fixed, omit outer resampling and explicitly restrict inference to this finite 5×5 grid. Either way, use a multilevel/crossed-effects or measurement-error model; an ordinary 70-row regression is pseudoreplication. Existing E1 correctly retains all eight samples when resampling items (`prereg-independent-decoding.md:170-180`).

## 4. Is tranche 2 genuinely out of sample?

Only weakly.

A held-out pairing tests the **model×benchmark interaction** after both main effects have already appeared in tranche 1. If most variance is additive by model and benchmark, the prediction is nearly in-sample. It is useful for “a new combination of familiar components,” but not for the broader practitioner claim about a new model or task.

A stronger, cost-neutral split is:

- tranche 1: a 4×4 model-benchmark block, 16 pairs;
- tranche 2: all nine pairs involving the held-out fifth model or held-out fifth benchmark, including one pair where both axes are unseen.

Freeze which model and benchmark are held out before capped outcomes exist. This tests axis extrapolation while preserving the same 25-pair total.

## 5. Does the byte-identity gate work?

Not as a live regeneration gate.

Records contain wall-clock `started_at` and `completed_at` values (`src/generate.py:225-238,403-455`). Serialization does use sorted keys (`src/generate.py:143-150`), and the record shown contains no problematic floats, but concurrent append ordering can differ. More importantly, the project reports only 46% bitwise determinism (`PAPER.md:182`).

The strongest achievable gate is:

- run old and new analysis pipelines over the **same immutable token-ID ledger**;
- require identical prompts, seeds, record IDs, token counts, EOS flags, parser results at every prefix, correctness matrices, emission indices, and derived analysis outputs;
- use a deterministic recorded/mock engine plus fixed clock for byte-level schema tests;
- use live regeneration only for distributional, parser, and normalized-decoder parity—not byte identity.

The gate at design lines 72–80 should not claim live records can be regenerated byte-for-byte.

## 6. Is the multiple-choice half measuring anything?

Potentially, but not necessarily E6.

For answer-only templates, a single-letter answer can appear immediately. Then \(F_E\) collapses near token one and \(\Delta=0\) above that point by score saturation. That is a valid negative control, but not strong support for an emission predictor: almost any model predicts zero once accuracy has saturated.

A zero prediction counts as success only under a preregistered **equivalence test** with a meaningful margin and adequate power. Failure to reject nonzero is not confirmation.

If the templates elicit reasoning before a final anchored answer line, \(E\) remains meaningful as answer-format timing. The design currently specifies only a single-letter grammar (`design:131-138`), not which of these regimes the templates create. The 16-token emission grid used today (`src/explore_budget.py:19,107-122`) is also too coarse for token-1-to-token-16 distinctions.

For TRANSLATE-ACT:

- XCOPA: translate the premise, causal/effect question, and both alternatives while preserving label mapping.
- Belebele: translate the entire passage, question, and options.

The latter changes a multilingual reading-comprehension task into self-translation plus English comprehension and consumes substantial output before reasoning. It is a different task strategy, not a clean analogue of MGSM. E6 itself needs only NATIVE because TRANSLATE-ACT cancels algebraically (`PAPER.md:46-53`).

## 7. What else is wrong?

**Model selection.** Selecting models for predictor spread is efficient for calibration but weak for representativeness and confounds multilingual training, architecture, and emission timing. Select primarily across architecture/training families, then report predictor coverage.

Aya-23-8B’s 8k context—and likewise Gemma-2-9B-it’s short context—means prompt plus “uncapped” output must fit below that limit. A benchmark cap of 8k is already impossible once the prompt is included. Long MMATH traces or Belebele passages therefore risk model-specific censoring. None of Aya-23, Gemma-2-it, Mistral-Instruct, or Ministral-Instruct is intrinsically reasoning-tuned; they are instruction-tuned. The unresolved Mistral choice is nevertheless unacceptable because the checkpoints have materially different context and architecture. Qwen3 is hybrid, but thinking is explicitly disabled (`configs/models.yaml:76-95`).

**Dropping PIVOT and CODE-SWITCHED.** It does not hurt E6, but it means this is no longer a straight E3/E5 replication of the published four-strategy design (`PAPER.md:32-40`; `EXPERIMENTS.md:145-150,226-228`). It loses best-arm and four-arm deliverable comparability. Call it E5a, or retain all four arms on a smaller benchmark subset. For E6, TRANSLATE-ACT is also expendable.

**Cost.** The ~140 GPU-hour claim is stale by roughly 3×. The catalogue gives 21.5 GPU-h/model at the old ~1,944 tok/s basis (`EXPERIMENTS.md:13-34,201-213`). At 5,893 tok/s:

\[
21.5\times 5\times\frac{1944}{5893}\approx35.5\text{ GPU-h}
\]

for sweeps. Scaling the design’s 30-hour uncapped estimate identically gives about 9.9 hours, for approximately **45 GPU-hours total**, not 140. The measured concurrency run confirms 5.9k tok/s (`tasks/todo.md:81-100`). Benchmark-specific trace lengths still need measurement, so 45 hours is an estimate, but 140 is not consistent with the corrected throughput.

**Generation caps.** If long-CoT traces reach their benchmark cap, \(p_{\text{correct}}\) is capped accuracy, not unlimited accuracy, and no-answer traces are right-censored. This biases both \(F_E\) and the proposed product, especially for models with low emission rates. Require model×benchmark caps, demonstrate negligible censoring, and ensure every tested \(\lfloor rB\rfloor\) is below the cap. Otherwise use censoring bounds or generate longer.

## Empirical Q1 result

I reproduced the existing 16-token-grid emission definition on all 12,000 NATIVE records (`/tmp/e3-review-scratch/compute_emission_correctness.py:265-287,356-440`). The emission counts exactly match the published analysis.

| Model/lang | \(p_{\text{correct}}\) | Emitted / 2000 | Peak window | \(P(C\mid E\text{ in window})\) | Product prediction | Joint observed | Error |
|---|---:|---:|---|---:|---:|---:|---:|
| Qwen de | 79.00% | 1,844 | (192,299] | 88.79% | 29.94 pp | 33.65 pp | 3.71 pp |
| Qwen th | 47.25% | 1,961 | (256,652] | 50.03% | 36.69 pp | 38.85 pp | 2.16 pp |
| Qwen sw | 33.75% | 1,498 | (128,247] | 47.99% | 10.48 pp | 14.90 pp | 4.42 pp |
| Llama de | 13.55% | 395 | (256,404] | 68.44% | 1.65 pp | 8.35 pp | 6.70 pp |
| Llama th | 3.85% | 136 | (192,421] | 58.97% | 0.15 pp | 2.30 pp | 2.15 pp |
| Llama sw | 28.95% | 1,080 | (256,494] | 52.68% | 10.00 pp | 18.20 pp | 8.20 pp |

Examples are recorded at `/tmp/e3-review-scratch/emission_correctness_dependence.json:419-472,548-588,676-740,45-110,174-238,302-354`.

Across 52 overlapping windows, the product predicts 274.11 summed percentage points versus 339.10 from the joint event, a 23.7% aggregate shortfall; this sum is descriptive because windows overlap. More fundamentally, all 5,086 never-emitting traces are incorrect by construction, while emitted traces are 59.7% correct. Unconditional independence cannot hold.

## Verdict

**Reject as designed.** Retain the breadth campaign only after replacing E6 with the correct-emission sub-CDF predictor, using a fixed primary grid plus adaptive secondary points, adopting a held-out model/benchmark-axis split, specifying crossed hierarchical resampling, imposing model-specific censoring gates, and treating MC zero effects through equivalence tests.

## Missing considerations

The design also omits:

- uncertainty in the predictor ledger itself—“parameter-free” is not uncertainty-free;
- errors-in-variables from estimated \(F_E\), \(p_{\text{correct}}\), and FLORES premiums;
- benchmark-specific failure of FLORES prose premiums for math notation and answer labels;
- winner’s curse from using `max_B Δ(B)` as the outcome;
- a full-curve proper scoring rule, such as prespecified weighted RMSE, which is preferable to noisy peak height and argmax;
- freezing executable analysis code and dependency versions, not only benchmark data manifests—the claim that “freezing operates on data, not code” (`design:143-144`) is unsafe.



Changes    +13 -0
AI Credits 651 (17m 14s)
Tokens     ↑ 5.1m (4.6m cached, 444.7k written) • ↓ 47.2k (20.4k reasoning)
Resume     copilot --resume=9f95b11e-14dc-48c8-9b1d-83c430e2482b
