#!/usr/bin/env python3
"""
Verify that clean and inject scenarios use different databases and produce different results.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_command(cmd: list) -> tuple[int, str]:
    """Run command and return (exit_code, output)."""
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return result.returncode, result.stdout + result.stderr

def main():
    print("=" * 80)
    print("SPRINT 3 SCENARIO VERIFICATION")
    print("=" * 80)
    
    # Step 1: Clean scenario
    print("\n[1/4] Running CLEAN scenario pipeline...")
    print("-" * 80)
    code, output = run_command([
        "python", "etl_pipeline.py", "run",
        "--run-id", "verify-clean",
        "--raw", "data/raw/policy_export_dirty.csv"
    ])
    
    if code != 0:
        print(f"ERROR: Clean pipeline failed with code {code}")
        print(output)
        return 1
    
    print(output)
    clean_log_path = ROOT / "artifacts" / "logs" / "run_verify-clean.log"
    if clean_log_path.exists():
        print("\n[CLEAN LOG]")
        print(clean_log_path.read_text())
    
    # Check database
    clean_db = ROOT / "chroma_db_clean"
    print(f"\n✓ Clean DB created: {clean_db.exists()}")
    
    # Step 2: Inject scenario
    print("\n[2/4] Running INJECT scenario pipeline...")
    print("-" * 80)
    code, output = run_command([
        "python", "etl_pipeline.py", "run",
        "--run-id", "verify-inject",
        "--raw", "data/raw/policy_export_dirty.csv",
        "--no-refund-fix",
        "--skip-validate"
    ])
    
    if code != 0:
        print(f"ERROR: Inject pipeline failed with code {code}")
        print(output)
        return 1
    
    print(output)
    inject_log_path = ROOT / "artifacts" / "logs" / "run_verify-inject.log"
    if inject_log_path.exists():
        print("\n[INJECT LOG]")
        print(inject_log_path.read_text())
    
    # Check database
    inject_db = ROOT / "chroma_db_inject"
    print(f"\n✓ Inject DB created: {inject_db.exists()}")
    
    # Step 3: Eval with clean scenario
    print("\n[3/4] Running EVAL with CLEAN scenario...")
    print("-" * 80)
    code, output = run_command([
        "python", "eval_retrieval.py",
        "--scenario", "clean",
        "--out", "artifacts/eval/verify_clean_eval.csv"
    ])
    
    if code != 0:
        print(f"ERROR: Clean eval failed with code {code}")
        print(output)
        return 1
    
    print(output)
    clean_csv = ROOT / "artifacts" / "eval" / "verify_clean_eval.csv"
    if clean_csv.exists():
        print(f"\n[CLEAN EVAL OUTPUT - First 3 rows]")
        lines = clean_csv.read_text().split('\n')
        for i, line in enumerate(lines[:3]):
            print(line)
    
    # Step 4: Eval with inject scenario
    print("\n[4/4] Running EVAL with INJECT scenario...")
    print("-" * 80)
    code, output = run_command([
        "python", "eval_retrieval.py",
        "--scenario", "inject",
        "--out", "artifacts/eval/verify_inject_eval.csv"
    ])
    
    if code != 0:
        print(f"ERROR: Inject eval failed with code {code}")
        print(output)
        return 1
    
    print(output)
    inject_csv = ROOT / "artifacts" / "eval" / "verify_inject_eval.csv"
    if inject_csv.exists():
        print(f"\n[INJECT EVAL OUTPUT - First 3 rows]")
        lines = inject_csv.read_text().split('\n')
        for i, line in enumerate(lines[:3]):
            print(line)
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON & VERIFICATION")
    print("=" * 80)
    
    # Read manifests
    clean_manifest = ROOT / "artifacts" / "manifests" / "manifest_verify-clean.json"
    inject_manifest = ROOT / "artifacts" / "manifests" / "manifest_verify-inject.json"
    
    if clean_manifest.exists():
        data = json.loads(clean_manifest.read_text())
        print(f"\n[CLEAN MANIFEST]")
        print(f"  scenario: {data.get('scenario')}")
        print(f"  chroma_path: {data.get('chroma_path')}")
        print(f"  cleaned_records: {data.get('cleaned_records')}")
    
    if inject_manifest.exists():
        data = json.loads(inject_manifest.read_text())
        print(f"\n[INJECT MANIFEST]")
        print(f"  scenario: {data.get('scenario')}")
        print(f"  chroma_path: {data.get('chroma_path')}")
        print(f"  cleaned_records: {data.get('cleaned_records')}")
    
    # Compare eval results
    if clean_csv.exists() and inject_csv.exists():
        import csv
        
        print(f"\n[EVAL RESULTS COMPARISON]")
        
        # Parse clean
        with open(clean_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            clean_rows = list(reader)
        
        # Parse inject
        with open(inject_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            inject_rows = list(reader)
        
        print(f"\nClean scenario results: {len(clean_rows)} questions evaluated")
        print(f"Inject scenario results: {len(inject_rows)} questions evaluated")
        
        if clean_rows and inject_rows:
            q1_clean = clean_rows[0]
            q1_inject = inject_rows[0]
            
            print(f"\n[Question 1 - CLEAN scenario]")
            print(f"  Question: {q1_clean.get('question', 'N/A')[:50]}...")
            print(f"  Top1 Doc ID: {q1_clean.get('top1_doc_id')}")
            print(f"  Contains Expected: {q1_clean.get('contains_expected')}")
            print(f"  Hits Forbidden: {q1_clean.get('hits_forbidden')}")
            
            print(f"\n[Question 1 - INJECT scenario]")
            print(f"  Question: {q1_inject.get('question', 'N/A')[:50]}...")
            print(f"  Top1 Doc ID: {q1_inject.get('top1_doc_id')}")
            print(f"  Contains Expected: {q1_inject.get('contains_expected')}")
            print(f"  Hits Forbidden: {q1_inject.get('hits_forbidden')}")
            
            # Count differences
            diffs = 0
            for i, (cq, iq) in enumerate(zip(clean_rows, inject_rows)):
                if cq.get('top1_doc_id') != iq.get('top1_doc_id') or \
                   cq.get('contains_expected') != iq.get('contains_expected'):
                    diffs += 1
            
            print(f"\n✓ Results differ in {diffs}/{len(clean_rows)} questions")
            if diffs > 0:
                print("  ✅ Different scenarios produce DIFFERENT results!")
            else:
                print("  ⚠️  Results are the same (may need larger test set)")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
