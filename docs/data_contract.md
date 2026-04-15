# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| policy_refund_v4 | Batch (CSV) | Trùng lặp nội dung `duplicate_chunk_text`, Thiếu ngày hiệu lực `missing_effective_date` | `quarantine_records` (theo từng loại lỗi) |
| hr_leave_policy | Batch (CSV) | Chính sách cũ/hết hạn `stale_hr_policy_effective_date` - bản 2025 | `stale_version_count` > 0 |
| legacy_catalog_xyz_zzz | Batch (CSV) | ID tài liệu không nằm trong danh mục cho phép `unknown_doc_id` | `quarantine_records` > 0 |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | … |
| doc_id | string | Có | … |
| chunk_text | string | Có | … |
| effective_date | date | Có | … |
| exported_at | datetime | Có | … |

---

## 3. Quy tắc quarantine vs drop

> Record bị flag đi đâu? Ai approve merge lại?

---

## 4. Phiên bản & canonical

> Source of truth cho policy refund: file nào / version nào?
