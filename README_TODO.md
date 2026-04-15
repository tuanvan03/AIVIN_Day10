# Your Project TODOs (By Sprints)

Follow these Sprints (each about 60 minutes) to complete this project. By the end, your pipeline should clean, assess, load, and document all its steps flawlessly.

## Sprint 1 (60') — Ingest & Schema
- **Objective:** Establish the raw data connection and build the source mappings.
- **Tasks:**
  - Locate and read the raw file at `data/raw/policy_export_dirty.csv`. You may create additional raw files.
  - Fill out the "Source Map" inside `docs/data_contract.md` (list at least 2 sources, identifying failure modes and metrics).
  - Test run the pipeline using `python etl_pipeline.py run --run-id sprint1`.
- **Definition of Done (DoD):** Your execution logs inside `artifacts/logs/` accurately dictate `raw_records`, `cleaned_records`, `quarantine_records`, and `run_id`.

---

## Sprint 2 (60') — Clean + Validate + Embed
- **Objective:** Modify the core data payload and establish expectation gates.
- **Tasks:**
  - Within `transform/cleaning_rules.py` and `quality/expectations.py`, add at least **3 new cleaning rules** and **2 new expectations**.
  - Prove your new rules have measurable impacts. E.g., make sure quarantining goes up when data is messy and expectations catch it. DO NOT only write trivial rules (like trailing space removal) without a proven scenario—this will lose points. Record this info into the `metric_impact` table in `reports/group_report.md`.
  - Ensure Chroma DB embedding acts idempotently (it should upsert based on `chunk_id` and remove obsolete IDs).
- **Definition of Done (DoD):** Executing `python etl_pipeline.py run` exits effectively (exit code 0). Expectations validate gracefully without halting the system (unless specifically instructed).

---

## Sprint 3 (60') — Inject Corruption & Generate Evidence
- **Objective:** Deliberately break things to prove your Quality Assurance safeguards work.
- **Tasks:**
  - Spoil your data: either purposefully add duplicates, mess up valid policies, or use the `--no-refund-fix --skip-validate` flags.
  - Run evaluation. Keep a record of the resulting evaluation (`artifacts/eval/`).
  - Compare the results (e.g., using `before_after_eval.csv` vs `after_inject_bad.csv` or creating a unified file with a scenario column).
  - Fully populate `docs/quality_report_template.md` saving as `docs/quality_report.md`. Capture screenshots snippets / logs into this document as evidence.
- **Definition of Done (DoD):** Provide documentation/figures that definitively prove that retrieval scores are drastically lower with bad data and improved heavily when your fixes apply (this is particularly relevant to the `q_refund_window` metric). Bonus points for demonstrating the same across HR versions `q_leave_version`.

---

## Sprint 4 (60') — Monitoring, Docs, Final Polish
- **Objective:** Write down the operations guidelines.
- **Tasks:**
  - Fill out all the documentation files in `./docs/`:
    - `pipeline_architecture.md`
    - `data_contract.md` 
    - `runbook.md`
  - Execute `python etl_pipeline.py freshness --manifest [path]` and decode PASS/WARN/FAIL into your `runbook.md`.
  - Assemble the `reports/group_report.md`.
  - Create an individual summary for every group member (using `reports/individual/template.md`).
- **Definition of Done (DoD):** README outlines "one single command" to execute the pipeline entirely. Cross-peer reviews for 3 group questions are placed correctly in `runbook.md` or `group_report.md`. 
