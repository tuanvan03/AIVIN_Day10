# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom
(Trường hợp giả định)
Bot IT Helpdesk trả lời **"12 ngày phép/năm"** (theo HR policy version cũ), trong khi HR đã ban hành version mới **10 ngày phép/năm**. Nhân viên dựa vào câu trả lời để đăng ký nghỉ vượt quota → HR phải đính chính thủ công và cập nhật lại đơn nghỉ phép.

---

## Detection

- **Expectation fail:** suite kiểm tra HR policy version phát hiện `effective_date` hoặc `doc_id` của bản cũ vẫn còn trong cleaned set → pipeline halt (hoặc log WARNING nếu chạy với `--skip-validate`).
- **Freshness check:** `python etl_pipeline.py freshness --manifest …` báo trạng thái theo SLA:
  - **PASS** — manifest mới nhất trong ngưỡng SLA, không có doc HR nào quá hạn.
  - **WARN** — có doc đã qua hạn cảnh báo nhưng chưa quá hạn cứng (cần rà, chưa chặn publish).
  - **FAIL** — HR policy cũ vẫn đang publish / manifest quá hạn SLA → bắt buộc xử lý.
- **Eval retrieval:** `eval_retrieval.py` cho câu `q_leave_version` có `hits_forbidden > 0` (top-k còn chunk chứa "12 ngày").

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Mở `artifacts/manifests/manifest_<run-id>.json`, kiểm tra `run_id`, danh sách `doc_id` HR và `effective_date` đang được publish | Xác định được run nào đưa HR bản cũ vào index; nếu thấy 2 doc_id HR cùng publish → xung đột version |
| 2 | Mở `artifacts/quarantine/*.csv` | HR version cũ phải nằm trong quarantine với lý do rõ ràng (vd: `superseded_hr_version`); nếu không có → rule quarantine không bắt được |
| 3 | Chạy `python eval_retrieval.py --out artifacts/eval/diag.csv` và đọc cột `hits_forbidden`, `top_k_text` cho `q_leave_version` | Nếu top-k còn chunk "12 ngày" → index chưa prune id cũ; nếu top-k toàn "10 ngày" nhưng bot vẫn sai → vấn đề ở tầng prompt/agent, không phải pipeline |

---

## Mitigation

1. **Rerun pipeline chuẩn** (không bỏ validate): `python etl_pipeline.py run --run-id hotfix-hr` — baseline đã upsert theo `chunk_id` và prune id không còn trong cleaned, nên HR bản cũ sẽ bị loại khỏi Chroma.
2. **Rollback embed** nếu rerun fail: chỉ trỏ agent sang manifest trước đó đã PASS (giữ lại `chroma_db` snapshot cũ), không publish manifest lỗi.
3. **Banner "data stale"** ở IT Helpdesk bot cho câu hỏi về leave policy trong thời gian khắc phục, tránh trả lời sai thêm.
4. **Xác nhận fix:** chạy lại `eval_retrieval.py`, `hits_forbidden` của `q_leave_version` phải về 0; freshness trả về PASS.

---

## Prevention

- **Expectation mới:** allowlist `doc_id` HR chỉ chấp nhận version mới nhất; fail ngay nếu thấy 2 version HR cùng cleaned set.
- **Cleaning rule:** quarantine bắt buộc mọi row HR có `effective_date` nhỏ hơn bản mới nhất (đã có baseline, cần thêm test chứng minh).
- **Alert freshness:** gắn owner HR policy trong `contracts/data_contract.yaml`; khi freshness = WARN/FAIL thì ping owner trước khi FAIL thành incident.
- **Peer review 3 câu (slide Phần E):**
  - Ai là owner của HR policy feed và SLA cập nhật bao lâu?
  - Nếu expectation halt lúc 2h sáng, ai rerun và theo quy trình nào?
  - Làm sao phát hiện sớm bot đang dùng version cũ trước khi user phàn nàn?
