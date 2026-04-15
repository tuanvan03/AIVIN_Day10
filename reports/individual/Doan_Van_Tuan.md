# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Đoàn Văn Tuấn  
**Vai trò:** Ingestion / Cleaning / Embed / Validation  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- Tệp `transform/cleaning_rules.py`: Chịu trách nhiệm clean raw data, tôi đã thêm 3 luật làm sạch mới liên quan đến quarantine chunk quá ngắn (< 15 kí tự), chặn rò rỉ số điện thoại PII (bằng regex `\b0[1-9]\d{8}\b`) và sửa lỗi nội dung SLA bị cũ (12 hours).
- Tệp `quality/expectations.py`: Xây dựng các expectation kiểm tra chất lượng bản ghi với cảnh báo Halt hoặc Warn. Cụ thể tôi đã bổ sung `chunk_min_length_8`, `no_pii_phone_numbers` và `sla_no_stale_12_hours`.
- Tệp `etl_pipeline.py`: Tôi phụ trách thực thi luồng để kết nối từ ingress đến lúc lưu vào thư mục `artifacts` và đẩy dữ liệu sạch lên vector store `chroma_db`. 

**Kết nối với thành viên khác:**

Tôi đã làm việc với thành viên viết logic Monitoring (`check_manifest_freshness`) nhằm đảm bảo sau khi `etl_pipeline.py` chạy cấu hình manifest sinh ra chuẩn xác để pipeline Freshness SLA của các bạn tích hợp trơn tru. Ngoài ra, việc chắt lọc qua các expectation của tôi đảm bảo bộ test eval có được lượng docs "sạch" nhất, giảm tỷ lệ `hits_forbidden` cho team RAG.

**Bằng chứng (commit / comment trong code):**

Tôi đã thêm [NEW RULE 2] trong `cleaning_rules.py`: `if re.search(r"\b0[1-9]\d{8}\b", text): ... (Quarantine chunk nếu phát hiện PII)` và expectation `no_pii_phone_numbers` ở `expectations.py` với severity `halt` giúp ngăn chặn pipeline hoạt động.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Một quyết định kỹ thuật quan trọng của tôi là việc sử dụng chiến lược linh hoạt giữa kiểm tra `halt` và `warn` trong file `expectations.py`. Thay vì đánh rớt cả tiến trình etl cho bất cứ lỗi nào, tôi sử dụng severity `warn` đối với lỗi văn bản hơi ngắn (`chunk_min_length_8`), vì văn bản 8-14 ký tự tuy ngắn nhưng chưa hẳn làm hỏng chức năng RAG, trong khi đó dùng `halt` cho lỗi chứa chữ số điện thoại nhạy cảm (PII) hoặc SLA bị sai ngày giờ (`sla_no_stale_12_hours`). Điều này giúp pipeline mạnh dạn chặn việc nhúng dữ liệu độc hại chưa kịp xử lý vào Vector Database của dự án. 
Thêm nữa, trong `etl_pipeline.py`, tôi đã áp dụng cách lưu trữ dữ liệu Quarantine ra file riêng biệt (`quarantine_{run_id}.csv`) để kỹ sư data có thể truy ngược lại lý do bị drop thay vì xoá bỏ vĩnh viễn.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

**Triệu chứng:** Pipeline đôi lúc bị văng và RAG trả đáp án có số điện thoại cá nhân trái phép hoặc chính sách phản hồi SLA 12h (thực tế 2026 năm nay quy định đã giảm xuống nhỏ hơn 12 giờ cho P1).
**Phát hiện:** Khi chạy `expectations.py` tôi thấy expectation `no_pii_phone_numbers` và `sla_no_stale_12_hours` fail với log: `[FAILED] no_pii_phone_numbers (severity: halt) -> violations=4` từ bộ kiểm tra test cases của sprint 2. Pipeline bị báo lỗi `PIPELINE_HALT`. 
**Khắc phục:** Tôi đã quay trở lại file `cleaning_rules.py` bổ sung logic loại bỏ (`quarantine`) toàn bộ chunk có khớp regex `r"\b0[1-9]\d{8}\b"` và tiến hành sửa lại văn bản SLA P1 chứa `12 hours` (hoặc loại hẳn đoạn đó để bot dựa vào văn bản đúng). Kết quả: khi chạy `python etl_pipeline.py run`, các bản ghi bị lệch chuẩn được push thẳng vào file `artifacts/quarantine/`, và tiến trình lưu embed db diễn ra an thành công `embed_upsert count=23`.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Sau khi triển khai luật, lượng dữ liệu bẩn được ngăn chặn:
**Run ID:** `2026-04-15T08-56Z` (và file manifest `manifest_2026-04-15T08-56Z.json`)
**Logs Pipeline thể hiện lượng Cleaned vs Quarantine:**
```
scenario=clean
raw_records=30
cleaned_records=23
quarantine_records=7
expectation[min_one_row] OK (halt) :: cleaned_rows=23
expectation[no_pii_phone_numbers] OK (halt) :: violations=0
expectation[sla_no_stale_12_hours] OK (halt) :: violations=0
PIPELINE_OK
```
Trong file `before_after_eval.csv` sinh ra, metric cho thấy `hits_forbidden` đã giảm xuống 0, và `expectation_fail_rate` biến mất.

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

Nếu được thêm 2 giờ, tôi sẽ viết bộ kiểm tra expectations này theo framework `Great Expectations` (hoạt động với JSON/YAML config) và gắn vào Pydantic validation cho các record sau khi clean. Việc này cho phép Data QA/Team Lead tự tuỳ chỉnh các luật config dễ dàng hơn việc sửa mã Python trong `cleaning_rules.py` hay `expectations.py` mỗi lần muốn đổi giới hạn (vd 12h -> 8h SLA).
