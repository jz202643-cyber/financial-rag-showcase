# Financial RAG — 50-Case Portfolio Benchmark

This benchmark contains 50 representative financial QA cases: 25 drawn from the development benchmark and 25 drawn from the broader evaluation set.

It is a **curated portfolio benchmark**, not a held-out generalisation test.

## Results

| Metric | Result |
|---|---:|
| Pipeline Completion | 50/50 (100.0%) |
| Route Accuracy | 40/50 (80.0%) |
| Status / Behaviour | 36/50 (72.0%) |
| Strict Case Accuracy | 31/50 (62.0%) |
| Structured Numeric | 18/28 (64.3%) |
| Unit Accuracy | 21/28 (75.0%) |
| Evidence Provenance | 21/28 (75.0%) |
| Safe Abstention | 14/15 (93.3%) |
| Narrative Content | 0/3 (0.0%) |

## Test Cases

| ID | Source | Category | Question | Strict Result |
|---|---|---|---|---|
| D_S01 | development_40 | structured_numeric | What was Meta's revenue in Q2 2026? | PASS |
| D_S02 | development_40 | structured_numeric | What was Meta's revenue in Q2 2025? | PASS |
| D_S03 | development_40 | structured_numeric | What were Meta's costs and expenses in Q2 2026? | PASS |
| D_S04 | development_40 | structured_numeric | What were Meta's costs and expenses in Q2 2025? | PASS |
| D_S05 | development_40 | structured_numeric | What was Meta's operating income in Q2 2026? | PASS |
| D_S06 | development_40 | structured_numeric | What was Meta's operating income in Q2 2025? | PASS |
| D_S07 | development_40 | structured_numeric | What was Meta's operating margin in Q2 2026? | PASS |
| D_S08 | development_40 | structured_numeric | What was Meta's operating margin in Q2 2025? | PASS |
| D_S09 | development_40 | structured_numeric | What was Meta's net income in Q2 2026? | PASS |
| D_S10 | development_40 | structured_numeric | What was Meta's capital expenditure in Q2 2026? | PASS |
| D_R01 | development_40 | structured_robustness | How much revenue did Meta report for Q2 2026? | PASS |
| D_R02 | development_40 | structured_robustness | What was Meta's operating profit in Q2 2026? | PASS |
| D_R03 | development_40 | structured_robustness | How large were Meta's total costs and expenses in Q2 2026? | PASS |
| D_N01 | development_40 | narrative | Why did Meta's operating income decline in Q2 2026? | FAIL |
| D_N02 | development_40 | narrative | Why did Meta increase capital expenditures? | FAIL |
| D_N03 | development_40 | narrative | What did Meta say about its 2026 capital expenditure outlook? | FAIL |
| D_N04 | development_40 | narrative | What was Meta's Q3 2026 revenue guidance? | FAIL |
| D_A01 | development_40 | abstention | What was Meta's cloud revenue in Q2 2026? | PASS |
| D_A02 | development_40 | abstention | What was Meta's AWS revenue in Q2 2026? | PASS |
| D_A03 | development_40 | abstention | What was Meta's banking revenue in Q2 2026? | PASS |
| D_A04 | development_40 | abstention | What was Meta's Q2 2027 revenue? | PASS |
| D_U01 | development_40 | unsupported | What is Meta's stock price target? | PASS |
| D_U02 | development_40 | unsupported | What is Meta's current share price? | PASS |
| D_U03 | development_40 | unsupported | How old is Meta's CEO? | PASS |
| D_U04 | development_40 | unsupported | How many Meta employees work in Europe? | PASS |
| H_S11 | original_50 | structured_numeric | How much cash flow from operations did Meta produce in Q2 2026? | FAIL |
| H_S12 | original_50 | structured_numeric | How much free cash flow did Meta generate during Q2 2026? | PASS |
| H_S13 | original_50 | structured_numeric | What was the combined balance of Meta's cash and marketable securities at June 30, 2026? | PASS |
| H_S14 | original_50 | structured_numeric | State Meta's long-term debt balance at the end of June 2026. | PASS |
| H_S15 | original_50 | structured_numeric | What was Meta's asset base as of June 30, 2026? | FAIL |
| H_S16 | original_50 | structured_numeric | How much revenue did Family of Apps generate in Q2 2026? | FAIL |
| H_S17 | original_50 | structured_numeric | What was Reality Labs revenue in the second quarter of 2026? | FAIL |
| H_S18 | original_50 | structured_numeric | How much operating income did Family of Apps produce during Q2 2026? | FAIL |
| H_S19 | original_50 | structured_numeric | What operating loss did Reality Labs report for Q2 2026? | FAIL |
| H_S20 | original_50 | structured_numeric | What was Meta's diluted earnings per share in Q2 2026? | FAIL |
| H_R06 | original_50 | structured_robustness | What was Meta's FCF for the June 2026 quarter? | PASS |
| H_R07 | original_50 | structured_robustness | How much liquidity did Meta hold in cash and marketable securities at quarter end? | PASS |
| H_R08 | original_50 | structured_robustness | What was Meta's long-term borrowing balance at June 30, 2026? | FAIL |
| H_R09 | original_50 | structured_robustness | How large was Meta's total asset base at the end of Q2 2026? | FAIL |
| H_R10 | original_50 | structured_robustness | What was Meta's bottom-line profit in Q2 2026? | FAIL |
| H_N01 | original_50 | narrative | What revenue range did Meta guide to for the third quarter of 2026? | FAIL |
| H_N02 | original_50 | narrative | What full-year 2026 capital expenditure range did management provide? | FAIL |
| H_N05 | original_50 | narrative | What investment area did Meta identify as an important driver of higher capital spending? | FAIL |
| H_A06 | original_50 | abstention | What was Meta's Q2 2026 cloud free cash flow? | PASS |
| H_A07 | original_50 | abstention | What was Meta's fintech revenue in Q2 2026? | PASS |
| H_A08 | original_50 | abstention | How much banking income did Meta earn in Q2 2026? | FAIL |
| H_A09 | original_50 | abstention | What was Meta's Q4 2026 revenue? | FAIL |
| H_A10 | original_50 | abstention | What was Meta's net income for 2027? | PASS |
| H_U04 | original_50 | unsupported | What is Mark Zuckerberg's current age? | PASS |
| H_U05 | original_50 | unsupported | What is Meta's market capitalization today? | PASS |
