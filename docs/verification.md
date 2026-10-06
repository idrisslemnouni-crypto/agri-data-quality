# Local verification — 5 October 2026

The complete workflow executed on real public source files; actual reports and plots were generated. The executed notebook's stored outputs contain no errors. Ruff lint/format, meaningful unit tests and dependency consistency passed.

A clean local Git clone was installed in a separate Python 3.12 study environment. The source acquisition and complete workflow ran from that clone without copied models or raw sources. Source scientific content was verified; generated JSON reports match exactly and tabular outputs reproduce within atol=rtol=1e-10. Clone tests, lint, notebook validation and pip check passed. This environment is shared by the four final studies with their scoped dependencies; it is not a dedicated fresh environment for each study.

All results are retrospective and limited to the documented source population. Historical notes above describe the pre-publication checkpoint; actual software CI runs are available in [GitHub Actions](https://github.com/idrisslemnouni-crypto/agri-data-quality/actions). No independent field validation, production deployment or invented metrics are claimed. Raw source files and any derived database/model are saved locally and ignored in Git. Source archives include code, documentation and actual reports, with acquisition commands to reconstruct ignored files.

## Input-contract verification — 6 October 2026

Numeric year/dekad representations now share a duplicate-key group before accepted rows reach SQLite. All conflicting rows retain their original source values in quarantine, and the report's duplicate count matches that quarantine rule. Seven local tests passed, including mixed numeric/text keys, source-audit counts, idempotent rebuilding, foreign keys and preservation of the previous database after a failed rebuild. Ruff lint and formatting checks passed.

The complete checksum-verified cached archive was processed into a temporary warehouse/report directory: 624,396 source rows (45,499 yield, 917 soil, 577,980 weather). The regenerated quality-report JSON matched the published report exactly; all 969 coverage rows matched at `atol=rtol=1e-10`. SHA-256 checks confirmed the existing report files were unchanged. No network acquisition or source/report replacement was needed. The actual source still has zero quarantine rows; artificial regression fixtures establish the new failure handling without inventing real-source defects. These are local checks of this change, not a claim of remote CI execution or field validity.
