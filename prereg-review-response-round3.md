# Response to Third-Round Review (GPT-5.6 Sol) — Changes in Prereg v0.4

Maps each round-3 item from `prereg-review-round3-gpt5.6-sol.md` to the change in `prereg-matched-budgets.md` v0.4.

## Required fixes

**1. Freeze the actual H1 budget before registration — adopted.** The conditional 1024/512 rule no longer survives into the registration: B* is derived once in week 1 (before registration) from the realized premiums and the **registered document states the number itself** (§5.3). B* is a listed registration field in the new §14. The "registered addendum" mechanism is deleted.

**2. Correct dollar-prefix evaluation — adopted, formula as given.** §5.2 now defines t_i(c) = min(n_i, ⌊(c − P_in·x_i)/P_out⌋) when input is affordable, so the evaluated prefix is capped at the stored trace length and never references ungeneratd tokens. EOS-complete (n_i < 4096) and censored (n_i = 4096, no EOS) traces are distinguished, with the constant-accuracy behavior for complete traces stated.

**3. Valid adjusted confidence procedure for H1 — adopted, via your third option.** q = 5 is now a separately corrected test: the family is **six tests** (H1-existence, H1-SESOI, H2, H3 × 3), each with its own raw p-value from sup-t inversion at its threshold (p(5) ≥ p(0) noted), Holm across the six. The SESOI claim is asserted only at its own Holm-local level; the invalid reuse of the q = 0 level is gone (§3, §7.3, §7.7, §8).

**4. Complete the power model — adopted, via your suggested simplification plus a joint-outcome fix.** The simulation now powers **H1-existence only at the fixed conservative allocation α/6** (smallest Holm-local level in the family), stated explicitly, so the other five tests and Holm's ordering need no modeling. The generative model is now **generation-level**: each simulated generation draws (correct\*, answer-emission index E), and accuracy at any prefix t is correct\*·1[E ≤ t] — so outcomes at the matched-token and FLORES-mapped prefixes of the same generation are jointly (deterministically, monotonically) determined, answering the nested-prefix dependence and FLORES-prefix questions. E is lognormal per (arm, language) anchored to published token-length distributions; independence of E and correct\* given the cell is a frozen, stated simplification. Dollar/H3 quantities are explicitly out of simulation scope under the α/6 allocation. **H1-SESOI power at a true 5-point effect is reported with the explicit caveat that it is expected to be low and is not a design target** (§8), and the same caveat is added to limitations (§13).

## Other issues

| Item | Resolution | Where |
|---|---|---|
| Vacuous censoring rule | Acknowledged and resolved by acknowledgment + removal: under the grid c_j = P_out×B_j, any instance with positive input cost has affordable count < 4096 at every grid point, so affordable prefixes are always fully observed and the v0.3 censoring support rule was vacuous — it is removed, censoring rates stay descriptive, and exploratory beyond-grid evaluation carries an explicit censoring caveat. | §5.2 |
| Data-dependent support | Resolved by showing it is not data-dependent under the corrected grid: feasibility depends only on input token counts, which are fixed by frozen prompts before any generation; therefore no within-resample support recomputation is needed, and this reasoning is stated in the document. | §5.2 |
| Conditional registration | New **§14 Registration completeness**: a field table (k + power, premiums, B*, price snapshot, dollar grid values, commit hashes, base_seed, prompt hashes, parser tables) that must hold realized values before filing; "no procedural placeholders in the registered version" is now an explicit rule, and Wk 1 of the timeline ends with filling §14 then registering. | §14, §12 |
| GlotLID fallback estimand | Fallback specified: stratified 10% human labeling per (arm × language) cell, cell compliance from its stratum with per-cell Wilson 95% intervals, stratum weights = cell sizes, explicitly flagged as an estimator change. | §6 |
| Parser malformed grouping | Strict grammar adopted: only syntactically valid locale-grouped integers or decimals with all-zero fractional part are accepted; malformed grouping is rejected as incorrect; the separator-stripping fallback is deleted (with your decimal-misparse rationale noted). | §4 |
| GlotLID per-cell blind spot | Validation sample enlarged to 240 (20/cell) with dual pass criteria: ≥ 95% overall AND ≥ 90% per cell. | §6 |
| MCB construction unnamed | Named and frozen: bootstrap analogue of Hsu's MCB — simultaneous upper bounds on each strategy's deficit-to-best via the item-clustered bootstrap with sup-t calibration over the four strategies. | §7.6 |
| Seed encoding | Byte-level spec frozen: SHA-256 over UTF-8 fields joined by 0x1F, first 8 digest bytes as big-endian unsigned 64-bit integer. | §10 |
