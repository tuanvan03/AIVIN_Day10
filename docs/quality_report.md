# Quality report — Lab Day 10 (nhóm)

**run_id:** `2026-04-15T10-32Z`  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

**Trước** = run `inject-bad` (`--no-refund-fix --skip-validate`, chroma `./chroma_db_inject`) · **Sau** = run `2026-04-15T10-32Z` (pipeline chuẩn, chroma `./chroma_db_clean`).

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | cùng file nguồn `data/raw/policy_export_dirty.csv` |
| cleaned_records | 6 | 6 | cờ `--no-refund-fix` chỉ đổi nội dung refund (14→7), không đổi số dòng |
| quarantine_records | 4 | 4 | rule quarantine (HR cũ, doc_id lạ, ngày không ISO, duplicate) chạy giống nhau ở cả 2 run |
| Expectation halt? | Không | Không | run "Trước" bị `--skip-validate` bypass nên không halt dù dữ liệu xấu; run "Sau" pass expectation thật sự |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới `artifacts/eval/before_after_eval.csv` (hoặc 2 file before/after).

AIVIN_Day10\artifacts\cleaned\cleaned_inject-bad.csv
AIVIN_Day10\artifacts\eval\before_after_eval.csv

**Câu hỏi then chốt:** refund window (`q_refund_window`)

**Trước** (`after_inject_bad.csv` — eval trên chroma `./chroma_db_inject`, run `inject-bad` với `--no-refund-fix --skip-validate`):
- `scenario = clean`, `top1_doc_id = policy_refund_v4`
- `top1_preview = "... trong vòng 7 ngày làm việc kể từ xác nhận đơn (ghi chú: bản sync cũ policy-v3 — lỗi migration). [cleaned: stale_refund_window]"`
- `contains_expected = yes`, `hits_forbidden = no`, `top1_doc_expected = (rỗng)`, `top_k_used = 3`

**Sau** (`before_after_eval.csv` — eval trên chroma `./chroma_db_clean`, run `2026-04-15T10-32Z` pipeline chuẩn):
- `scenario = clean`, `top1_doc_id = policy_refund_v4`
- `top1_preview = "... trong vòng 7 ngày làm việc kể từ xác nhận đơn (ghi chú: bản sync cũ policy-v3 — lỗi migration). [cleaned: stale_refund_window]"`
- `contains_expected = yes`, `hits_forbidden = no`, `top1_doc_expected = (rỗng)`, `top_k_used = 3`

**Kết luận:** với data export hiện tại, cả 2 run đều có top-1 đúng (`7 ngày`) và `hits_forbidden = no`. Nhìn `top1_preview` có marker `[cleaned: stale_refund_window]` — chứng tỏ rule cleaning đã phát hiện và gắn nhãn stale trên dòng refund, đây là bằng chứng pipeline đang làm việc. Tuy nhiên, do eval hiện tại không sinh chênh lệch số liệu giữa 2 collection, mục 5 ghi nhận gap này để bổ sung kịch bản inject mạnh hơn ở lần sau.

---

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, `top1_doc_expected`)

**Trước** (`after_inject_bad.csv`):
- `top1_doc_id = hr_leave_policy`, `top1_preview = "Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."`
- `contains_expected = yes`, `hits_forbidden = no`, `top1_doc_expected = yes`, `top_k_used = 3`

**Sau** (`before_after_eval.csv`):
- `top1_doc_id = hr_leave_policy`, `top1_preview = "Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026."`
- `contains_expected = yes`, `hits_forbidden = no`, `top1_doc_expected = yes`, `top_k_used = 3`

**Kết luận:** câu `q_leave_version` **không thay đổi giữa 2 run** vì cờ `--no-refund-fix` chỉ ảnh hưởng refund window, không chạm vào HR policy — baseline đã quarantine đúng bản HR cũ ngay từ cleaning. Để có merit rõ rệt cho dòng này, cần inject thêm kịch bản tác động vào HR (vd: tạm tắt rule quarantine HR, hoặc inject thêm row HR cũ vào raw).

---

## 3. Freshness & monitor

**Kết quả:** `FAIL`

```json
{
  "latest_exported_at": "2026-04-10T08:00:00",
  "age_hours": 121.802,
  "sla_hours": 24.0,
  "reason": "freshness_sla_exceeded"
}
```

**SLA đã chọn:** `sla_hours = 24h` — dữ liệu policy phải được export lại trong vòng 24 giờ gần nhất để agent luôn đọc bản mới. Ngưỡng 24h phù hợp với tần suất cập nhật HR / CS policy (thường không đổi trong ngày, nhưng cần refresh hằng ngày để bắt kịp bản sửa đổi).

**Diễn giải:**
- `latest_exported_at = 2026-04-10T08:00:00` — thời điểm export cuối cùng của nguồn raw.
- `age_hours = 121.8h` (~5 ngày) — dữ liệu đã quá hạn SLA gấp **~5 lần** (121.8 / 24).
- `reason = freshness_sla_exceeded` → monitor trả `FAIL`, pipeline cần **chặn publish** (hoặc gắn banner "data stale") cho đến khi có export mới.

**Quy ước 3 mức:**
- **PASS** — `age_hours ≤ sla_hours` → publish bình thường.
- **WARN** — `sla_hours < age_hours ≤ 2 × sla_hours` → ping owner feed, chưa chặn.
- **FAIL** — `age_hours > 2 × sla_hours` (hoặc theo reason khác) → chặn publish / rollback về manifest gần nhất còn PASS.

---

## 4. Corruption inject (Sprint 3)

> Mô tả cố ý làm hỏng dữ liệu kiểu gì (duplicate / stale / sai format) và cách phát hiện.
- Sử dụng argument `--no-refund-fix` và `--skip-validate` được implement sẵn, được phát hiện nhờ các file log csv và json trong `artifacts\` có đề mục `scenario` để ghi lại xem có sử dụng inject hay không.
---

## 5. Hạn chế & việc chưa làm

- Freshness FAIL do raw cũ, không do pipeline: age_hours=121.8h là vì file raw policy_export_dirty.csv export từ 2026-04-10, không phải do pipeline lỗi. Trong môi trường thật, cần process upstream refresh raw hằng ngày — hiện lab chưa mô phỏng bước này.
