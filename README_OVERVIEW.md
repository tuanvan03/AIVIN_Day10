# README Overview: Project Setup and Goals

## 1. Context & Motivation
This is the Day 10 lab of the AI in Action course, focusing on **Data Pipeline & Data Observability**. 

Previous labs (Day 08 & Day 09) covered RAG and Multi-agent architectures. However, those layers are only effective if the underlying data pipeline (Ingest → Clean → Validate → Publish) is reliable. 

In this lab, you simulate handling raw data exported from a source system (like an HR database exporting `policy_export_dirty.csv`). This data will contain errors such as:
- Duplicates
- Missing effective dates
- Suspicious document IDs
- Non-ISO effective date formats
- HR policy versioning conflicts (e.g., old vs. new leave days)
- Chunking errors (e.g., wrong refund windows: 14 vs 7 days)

Your goal is to build an ETL layer that handles these corruptions robustly, providing logs, quarantining bad records, and proving improvement with before-and-after evaluations.

---

## 2. Learning Objectives
By the end of this project, you will:
1. **Ingest and Map Schema**: Load dirty data and log initial counts.
2. **Clean and Quarantine**: Identify dirty records, clean what you can, and move the rest to a quarantine zone.
3. **Validate Rules (Expectations)**: Run an expectation suite to prevent destructive updates from reaching the downstream vector store.
4. **Embed Successfully**: Cleaned data should be stored safely into a Chroma DB vector store.
5. **Observability**: Provide freshness checks, runbooks, and evidence of quality improvements across runs.

---

## 3. Directory Structure Summary
- `etl_pipeline.py`: Main executable that runs the whole data pipeline.
- `eval_retrieval.py`: Used to evaluate your RAG results on CSV before and after your fixes.
- `transform/`: Houses your data cleaning rules.
- `quality/`: Houses your validation rules (expectations suite).
- `monitoring/`: Monitors freshness and data SLA.
- `contracts/`: YAML configuration defining the layout and quality expected for data.
- `docs/ & reports/`: Where you document your pipeline architecture, runbook, and findings.
- `data/`: Contains raw CSV data and evaluation/grading questions.
- `artifacts/`: Generated results (manifests, logs, quarantined CSVs, retrieval metrics). This folder proves the engine works and should be preserved or git-ignored based on the instructions.

Continue to `README_ARCHITECTURE.md` for details on how these components connect!
