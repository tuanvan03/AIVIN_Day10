# Execution Workflow
How to install, setup, and run this pipeline from end to end.

## 1. Setup Environment
First, ensure you have Python 3 and setup a virtual environment:

```bash
# Inside the "day10/lab" directory
python -m venv .venv

# Activate it
source .venv/bin/activate       # On Mac/Linux
# .venv\Scripts\activate        # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

*(Note: The first time it runs, SentenceTransformers will download the `all-MiniLM-L6-v2` model, requiring ~90MB of data and an internet connection.)*

---

## 2. Standard Run
A standard, clean run of the pipeline will extract the raw data, apply all cleaning rules (such as deduplication and formatting), run expectations against it, and embed it into Chroma DB.

**Run the pipeline:**
```bash
python etl_pipeline.py run
```
You should see logging metrics printed directly to your console, confirming counts for `raw_records`, `cleaned_records`, and `quarantine_records`. Check `artifacts/manifests` folder to obtain your `<run-id>`.

**Check Freshness:**
To ensure your data isn't stale, run a freshness check against the generated manifest file.
```bash
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json
```

**Evaluate Retrieval Results:**
Now, test if the newly ingested vector data provides correct answers to test questions!
```bash
python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
cat artifacts/eval/before_after_eval.csv
```

---

## 3. Injecting Corrupt Data (Testing Mode)
In Sprint 3, you'll need to demonstrate what happens when bad data flows through unmodified. The prompt below instructs the pipeline to ignore the refund-window fix and skip validation halts.

**Run pipeline with intentional corruption:**
```bash
python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
```

**Evaluate after bad-injection:**
```bash
python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv
```
You can then examine `after_inject_bad.csv` and compare it with the results obtained during the Standard Run to see how much retrieval degrades with bad data.

---

## 4. Grading
When it is time for evaluation (after 17:00), there is a grading script the instructor provided. 
```bash
python grading_run.py --out artifacts/eval/grading_run.jsonl
```

For Instructors / Quick Checks:
```bash
python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl
python instructor_quick_check.py --manifest artifacts/manifests/manifest_<run-id>.json
```

Proceed to `README_TODO.md` to see instructions for your sprints!
