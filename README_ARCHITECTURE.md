# System Architecture & Roles

## 1. Overall Pipeline Architecture
The pipeline is designed as an **ETL (Extract, Transform, Load)** script that includes robust Quality Assurance steps.

The data flow runs strictly in this order:
```text
Raw Export (CSV)  →  Clean (Transform)  →  Validate (Expectations)  →  Embed (Chroma DB)  →  Serving (RAG/Agents)
```

1. **Ingest Phase**: Reads `data/raw/policy_export_dirty.csv`.
2. **Clean Phase**: Processes records using `transform/cleaning_rules.py`. Valid data goes to `artifacts/cleaned/`, invalid/unfixable data goes down a separate path to `artifacts/quarantine/`.
3. **Quality Phase**: Runs `quality/expectations.py` over your cleaned dataset. If critical rules (`halt` expectations) fail, the pipeline stops here to prevent poisoning the database.
4. **Embed Phase**: Once validated, the data is pushed (upserted idempotently by `chunk_id`) to ChromaDB for downstream models to use. Old non-matching vectors should be automatically pruned.
5. **Monitor Phase**: Final manifests describing the run and freshness metrics are saved in `artifacts/manifests/` and checked using `monitoring/freshness_check.py`.

---

## 2. Team Member Roles
If working in a team, assigning specific zones to individuals can speed up development:

| Role | Responsibility and Focus areas |
|---|---|
| **Ingestion Owner** | Handle the raw paths, coordinate logging features, and generate execution manifests. Maintains `contracts/data_contract.yaml`. |
| **Cleaning / Quality Owner** | Maintain `transform/cleaning_rules.py` and `quality/expectations.py`. Write standard cleaning techniques and manage the quarantine queue. |
| **Embed Owner** | Manages `chromadb` collection ingestion. Ensures indexing is idempotent. |
| **Monitoring / Docs Owner** | In charge of the `monitoring/freshness_check.py`, maintaining `runbook.md`, and pulling together the final system group report. |

---

## 3. Dealing with Architecture failures (Debugging Priority)
If data doesn't seem right to the downstream agents, follow this investigation hierarchy:
1. **Freshness / Version**: Is the system using the absolute latest ingestion manifest run? Was it ingested today?
2. **Volume & Errors**: Did the ingest actually load 100 rows, or only 5? Check logs and quarantine stats.
3. **Schema & Contract**: Is the column named differently than what the expectation expected?
4. **Lineage / run_id**: Make sure the run ID traces successfully through clean -> manifest -> db.
5. *(Finally)* **Model/Prompt**: Only AFTER steps 1-4 are verified should you adjust LLM prompts or models.

Continue to `README_WORKFLOW.md` to see exactly how to execute this pipeline.
