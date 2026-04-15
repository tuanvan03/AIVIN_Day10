# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` | Batch CSV load qua `load_raw_csv` (UTF-8, DictReader) | Header sai / file thiếu / encoding hỏng | `raw_records` trong log + exit 1 nếu file missing |
| `data/docs/*.txt` (canonical) | Tham chiếu trong `contracts/data_contract.yaml → canonical_sources` | Lệch version so với export (vd refund 14 vs 7 ngày) | Expectation `refund_no_stale_14d_window` halt |
| Chroma collection `day10_kb` | `col.upsert` theo `chunk_id` + prune id cũ | Đổi `EMBEDDING_MODEL` giữa các run → trộn vector space | `embed_upsert count`, `embed_prune_removed` trong log |
| Manifest `artifacts/manifests/manifest_*.json` | Ghi sau embed (freshness watermark) | `latest_exported_at` > SLA | `freshness_check=FAIL` → `#data-quality-alerts` (SLA 24h) |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | `{doc_id}_{seq}_{sha256(doc_id\|chunk_text\|seq)[:16]}` — khóa upsert vào Chroma |
| doc_id | string | Có | Phải thuộc `allowed_doc_ids` trong contract; ngoài allowlist → quarantine `unknown_doc_id` |
| chunk_text | string | Có | Nội dung sau clean/fix (refund 14→7, SLA 12h→4h); `min_length=8`, không chứa SĐT VN |
| effective_date | date | Có | Chuẩn hoá về `YYYY-MM-DD` (nhận thêm `DD/MM/YYYY`); HR phải ≥ `2026-01-01` |
| exported_at | datetime | Có | ISO từ source; dùng cho `latest_exported_at` trong manifest → freshness SLA |

---

## 3. Quy tắc quarantine vs drop

Toàn bộ record bị loại trong `clean_rows` đều **quarantine** (không drop vĩnh viễn) — ghi ra `artifacts/quarantine/quarantine_<run_id>.csv` kèm cột `reason`.

| Reason | Severity | Hành động |
|--------|----------|-----------|
| `unknown_doc_id` | Quarantine | Owner review: nếu là doc mới → cập nhật `allowed_doc_ids` + `canonical_sources` rồi rerun |
| `missing_effective_date` / `invalid_effective_date_format` | Quarantine | Fix tại source export hoặc bổ sung rule parse |
| `stale_hr_policy_effective_date` | Quarantine | Bỏ hẳn (version HR cũ, không merge lại) |
| `missing_chunk_text` | Quarantine | Drop de-facto (chunk rỗng, không có gì để cứu) |
| `chunk_too_short` (<15 ký tự) | Quarantine | Review thủ công; ghép với chunk kế nếu cần |
| `contains_pii_phone` | Quarantine | Bắt buộc redact SĐT trước khi merge lại |
| `duplicate_chunk_text` | Quarantine | Bỏ (giữ bản đầu tiên đã vào cleaned) |

- **Approver merge lại:** owner team `nhóm 3-E402` (xem `contracts/data_contract.yaml → owner_team`).
- **Cách merge:** sửa tại source → đưa row đã fix trở lại `data/raw/policy_export_dirty.csv` → rerun `python etl_pipeline.py run` (idempotent theo `chunk_id`).

---

## 4. Phiên bản & canonical

Source of truth được khai báo tại `contracts/data_contract.yaml → canonical_sources`:

| doc_id | Canonical file | Ràng buộc version |
|--------|----------------|-------------------|
| `policy_refund_v4` | `data/docs/policy_refund_v4.txt` | Cửa sổ refund = **7 ngày làm việc** (v4). Xuất hiện `14 ngày làm việc` → fix hoặc halt `refund_no_stale_14d_window` |
| `sla_p1_2026` | `data/docs/sla_p1_2026.txt` | Resolution P1 = **4 hours**. `12 hours` → fix hoặc halt `sla_no_stale_12_hours` |
| `it_helpdesk_faq` | `data/docs/it_helpdesk_faq.txt` | — |
| `hr_leave_policy` | `data/docs/hr_leave_policy.txt` | `effective_date ≥ 2026-01-01` (xem `policy_versioning.hr_leave_min_effective_date`); không chứa marker `10 ngày phép năm` |

Contract version hiện tại: `1.0` (`contracts/data_contract.yaml`). Mọi thay đổi allowlist/canonical **phải bump version** và đồng bộ cả `cleaning_rules.py` + `expectations.py`.