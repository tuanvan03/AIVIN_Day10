# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhóm-03-E402  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Lê Nguyễn Thanh Bình | Ingestion / Raw Owner | thanhbinh.lenguyen.1208@gmail.com |
| Đoàn Văn Tuấn | Cleaning & Quality Owner | doantuanvan2003@gmail.com |
| Ninh Quang Trí | Embed & Idempotency Owner | nq.tri2511@gmail.com |
| Vũ Minh Khải | Monitoring | vmkqa2@gmail.com |

**Ngày nộp:** 15/04/2026
**Repo:** https://github.com/tuanvan03/AIVIN_Day10
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

- Nguồn raw là CSV mẫu `data/raw/policy_export_dirty.csv` — export giả lập từ hệ nguồn (policy / SLA / HR / IT Helpdesk) với 10 dòng đã cấy sẵn các failure mode: duplicate, thiếu `effective_date`, `doc_id` không thuộc allowlist (`legacy_catalog_xyz_zzz`), ngày định dạng DMY (`01/02/2026`), version HR cũ (10 ngày phép, eff=2025), và cửa sổ refund sai 14 ngày. 

- Pipeline chạy tuần tự **ingest → clean → validate → embed → manifest → freshness** trong `etl_pipeline.py`: `load_raw_csv` đọc CSV, `clean_rows` áp dụng rule (allowlist, chuẩn hoá ngày ISO, quarantine HR stale, dedupe, fix refund 14→7, rule mới: short-chunk, PII phone, fix SLA `12 hours`→`4 hours`), `run_expectations` chạy 8 expectation (halt/warn), sau đó upsert vào Chroma theo `chunk_id` + prune id cũ, cuối cùng ghi manifest JSON và check freshness theo SLA. 

- `run_id` được log ở dòng đầu mỗi file `artifacts/logs/run_<id>.log` (ví dụ `run_id=2026-04-15T10-32Z`) và cũng nằm trong manifest.

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

```bash
python etl_pipeline.py run && python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json && python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
```

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Rule `chunk_too_short` (<15 ký tự) | quarantine=0 (không filter) | quarantine +3 trên test 30-case (#21,22,23) | `transform/cleaning_rules.py:118-121` + stdout test |
| Rule `contains_pii_phone` (regex `0[1-9]\d{8}`) | quarantine=0, PII lọt vào cleaned | quarantine +3 trên test 30-case (#24,25,26) | `transform/cleaning_rules.py:123-125` |
| Rule fix SLA `12 hours` → `4 hours` (`sla_p1_2026`) | chunk còn chứa `12 hours` (violate E8) | 2 chunk được fix, gắn marker `[cleaned: sla_response_time]` | `transform/cleaning_rules.py:143-146` |
| Expectation `no_pii_phone_numbers` (halt) | baseline không có; PII lọt qua validate | fail với `violations=4` trên test 30-case | `quality/expectations.py:115-128` |
| Expectation `sla_no_stale_12_hours` (halt) | baseline không có; chunk 12h embed vào KB | fail với `violations=2` trên test 30-case | `quality/expectations.py:131-145` |

**Rule chính (baseline + mở rộng):**

- **Baseline (cleaning):** allowlist `doc_id` ∈ {policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy}; chuẩn hoá `effective_date` về `YYYY-MM-DD` (chấp nhận ISO và `DD/MM/YYYY`); quarantine HR có `effective_date < 2026-01-01`; quarantine `chunk_text` rỗng / `effective_date` rỗng; dedupe theo text đã chuẩn hoá (strip + lower); fix `policy_refund_v4` chứa `14 ngày làm việc` → `7 ngày làm việc`.
- **Mở rộng (3 rule mới):** chunk quá ngắn (<15), chứa số điện thoại PII, fix SLA `12 hours` → `4 hours` cho `sla_p1_2026`.
- **Expectation (8):** `min_one_row` (halt), `no_empty_doc_id` (halt), `refund_no_stale_14d_window` (halt), `chunk_min_length_8` (warn), `effective_date_iso_yyyy_mm_dd` (halt), `hr_leave_no_stale_10d_annual` (halt), **`no_pii_phone_numbers` (halt — mới)**, **`sla_no_stale_12_hours` (halt — mới)**. Toàn bộ expectation mới đều ở mức **halt**.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Run `inject-bad` (`python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`) cho kết quả `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1` trong `artifacts/logs/run_inject-bad.log:10`. Cách xử lý: vì chỉ là demo Sprint 3 nên dùng `--skip-validate` để pipeline vẫn embed (để đo suy giảm retrieval); trong run chuẩn, chỉ cần bật lại fix (bỏ `--no-refund-fix`) là rule `fix refund 14→7` đưa chunk về `7 ngày làm việc` và expectation pass (xem log `run_2026-04-15T10-32Z.log:10`).

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Chạy song song hai pipeline, ghi vào hai Chroma collection tách biệt (`chroma_db_clean` / `chroma_db_inject`) để so sánh retrieval:

- **Clean (after fix):** `python etl_pipeline.py run` — áp dụng đầy đủ rule, refund được fix 14→7, 8/8 expectation pass. Log: `artifacts/logs/run_2026-04-15T10-32Z.log`.
- **Inject (before fix):** `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` — tắt rule fix refund và bỏ qua halt, chủ ý embed chunk stale `14 ngày làm việc`. Log: `artifacts/logs/run_inject-bad.log`.

**Kết quả định lượng (từ CSV / bảng):**

| Chỉ số | Clean run | Inject run |
|---|---|---|
| `raw_records` / `cleaned_records` / `quarantine_records` | 10 / 6 / 4 | 10 / 6 / 4 |
| `refund_no_stale_14d_window` | **OK** (violations=0) | **FAIL** (violations=1) |
| 7 expectation còn lại | OK | OK |
| Embed | upsert 6 vào `day10_kb` | upsert 6 nhưng chứa chunk stale 14 ngày |

Bằng chứng retrieval tại `artifacts/eval/before_after_eval.csv` (scenario=clean): câu `q_refund_window` trả về top1 `policy_refund_v4` với preview chứa "7 ngày làm việc [cleaned: stale_refund_window]", `contains_expected=yes`, `hits_forbidden=no`. Câu `q_leave_version` top1 `hr_leave_policy` preview "12 ngày phép năm theo chính sách 2026", `top1_doc_expected=yes` — cho thấy rule HR stale + fix refund đã chặn bản cũ khỏi index. Với run inject, expectation fail ngay ở tầng validate (log dòng 10) → ngăn được việc publish chunk sai lên collection chuẩn nếu không cố ý `--skip-validate`.

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

**SLA chọn:** `FRESHNESS_SLA_HOURS = 24` (đặt trong `.env`, đọc ở `etl_pipeline.py:129`). Nghĩa là `latest_exported_at` ghi trong manifest phải cách thời điểm check không quá 24 giờ — phù hợp với batch ingest hằng ngày của pipeline policy/HR/SLA.

**Cơ chế check:** `monitoring/freshness_check.py` đọc `latest_exported_at` từ manifest, parse ISO (chấp nhận `...Z` và naive → coi là UTC), tính `age_hours = now − latest_exported_at`, rồi trả về một trong ba trạng thái:

- **PASS** — `age_hours ≤ sla_hours`. Dữ liệu còn tươi, pipeline an toàn để phục vụ retrieval.
- **WARN** — manifest không có trường timestamp hợp lệ (`no_timestamp_in_manifest`). Không đủ dữ liệu để kết luận → cần điều tra ingest/logging.
- **FAIL** — manifest thiếu file (`manifest_missing`) hoặc `age_hours > sla_hours` (`freshness_sla_exceeded`). Đây là tín hiệu chặn đầu tiên trong debug order (Freshness → Volume → Schema → Lineage → Model).

**Manifest mẫu:** `artifacts/manifests/manifest_2026-04-15T10-32Z.json` có `latest_exported_at=2026-04-10T08:00:00` → check cho kết quả `FAIL` với `age_hours=122.553`, `sla_hours=24.0`, `reason=freshness_sla_exceeded` (log dòng 18) — đúng kỳ vọng vì CSV mẫu được export cách ngày nộp 5 ngày.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Có.
- Trỏ agent Day 09 sang chroma_db_clean/day10_kb thay cho collection cũ → agent đọc đúng bản đã clean + validate + fix refund/HR.
- Mỗi chunk có metadata run_id + effective_date → trace được "agent trả lời dựa trên run nào"

_________________

---

## 6. Rủi ro còn lại & việc chưa làm
Rủi ro:
- Chưa cố định model, sẽ lỗi nếu như lần khác vô tình đổi model, dữ liệu được chèn vào sẽ vector database sẽ gồm 2 loại vector từ 2 model khác nhau -> kết quả search sẽ tệ.
Việc chưa làm:
- Thời gian làm việc khá gấp, nên việc đánh giá nhóm làm có vẻ chưa tốt lắm, kết quả giống nhau với 'clean run' và 'inject run'. Có thể là phần 'inject run' chưa tốt hoặc sai ở đâu đó. Nếu có thể thì sẽ tập trung làm lại phần này.




