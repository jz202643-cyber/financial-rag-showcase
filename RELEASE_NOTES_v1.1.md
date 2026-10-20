# Financial RAG Showcase v1.1 — Candidate Release Notes

**Status:** release candidate. This package has not been published to the GitHub repository.

## Scope

A narrow reliability update to the publicly demonstrated RAG pipeline. The `main.py` showcase routing/fallback behavior is retained, rather than replaced by the different, experimental research entrypoint.

### Changes

1. **Cell-level unit inference.** Integrates the research fix for mixed monetary/percentage rows. A percentage-change cell no longer contaminates monetary facts in the same table row. Adds whole-word metric semantics and `USD per share` handling for earnings-per-share values.
2. **Qualifier parsing across registered metrics.** Integrates research qualifier v2 (pre-/post-metric) with a scoped suffix handler that ignores reporting-period and explicit comparison clauses. Known segments (Reality Labs, Family of Apps) remain separate from unknown qualifiers.
3. **Comparison safety.** Explicit comparison questions now abstain in the structured path rather than returning just one period's fact as a complete comparison.
4. **Historical data corrections.** Four source-supported `unit` changes in `data/meta_q2_2026_financial_facts.json`: facts `_0009`, `_0010` (Provision for income taxes: `percent` → `USD millions`), and `_0015`, `_0016` (Diluted EPS: `percent` → `USD per share`). All 168 entries were retained and all other fields preserved.
5. **Ingestion dependency repair.** Adds the three `ingestion/tables/` parser modules required by the existing `financial_fact_builder.py`, so unit extraction can be imported and tested.
6. **Offline regression tests and demo cases.** Adds tests for qualifiers, unit correctness, JSON fact-unit sanity, main structured-path behavior, and examples of safe abstention.

### Verification performed

- **42 passed / 0 failed** in targeted `pytest` suite (with real structured routing and fact data; heavyweight narrative retrieval/generation imports stubbed for structured tests).
- `compileall` passed for Python modules.
- Offline smoke comparison on the 43 questions **expected to be non-narrative** in the existing 50-case curated benchmark: route agreement **36/43** and status agreement **35/43** for both the old showcase and this candidate. One case in each version routes to narrative and raises a stub-induced `KeyError` in this smoke harness. This is a **compatibility smoke comparison, not a valid re-run of the benchmark**.
- No other benchmark category outcomes or percentages have been recomputed for v1.1.

### Benchmark transparency

`evaluation/benchmark_50_portfolio_results.json` and `.md` are **historical initial-showcase results**. They are kept unchanged for provenance and must not be presented as v1.1 performance. Rerun the full benchmark in an environment with `bm25s`, `sentence-transformers`, model weights and (where relevant) narrative LLM credentials, and review case-level results before changing the reported metrics.

### Remaining limitations

- Natural-language qualifier resolution remains heuristic, not general semantic entailment.
- Recognized segment detection does not imply complete segment-level fact extraction.
- Multi-period comparisons, period normalization, cross-page extraction and narrative-answer quality have not been independently certified by this patch.
- Existing deterministic fallback and showcase-domain rules remain in place, including a minimal defensive keyword fallback for aliases unrecognized by the metric registry.
- No ingestion pipeline rerun has been performed here. The four JSON fact-unit corrections are targeted source-supported edits, **not** a complete regenerated fact store.

### Safe publishing procedure

Review the changes in this ZIP against your **current local** `financial-rag-showcase` checkout, merge selectively, run tests (and the full 50-case benchmark when dependencies are ready), then commit and push. Preserve your research repository separately. Do not upload `.env`, credentials, cache directories, private files or raw development archives.
