# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Ninh Quang Trí <br>
**Vai trò:** Ingestion  <br>
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

`etl_pipeline.py`, `artifacts/`

**Kết nối với thành viên khác:**

Bổ sung scenario vào file `etl_pipeline.py` của Tuấn để xuất ra csv

**Bằng chứng (commit / comment trong code):**

`a36ded0049c7ab0e45f00683a82303f8cbcbd8e4`, `1c2ab3cfa5590c29cbe7152e686badde049a780e`, `2087a9ed53f44d3b454a79c96d2a63e11050266c`, `cb81c214add277df043378f9ea9f704dc209f541`

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> Chọn 2 option cho scenario là `clean` và `inject` và thay đổi file `etl_pipeline.py` để khi run với inject và clean thì sẽ xuất ra các file eval, logs, manifests, quarantine để so sánh.

_________________

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Lỗi conflict metaclass giữa thư viện `sentence-tranformers` và `transformers` nên không thể chạy eval

_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

> `standard,q_lockout,query: Bao nhiêu lần đăng nhập sai thì tài khoản bị khóa?,it_helpdesk_faq,passage: Tài khoản bị khóa sau 5 lần đăng nhập sai liên tiếp.,yes,no,,3
standard,q_leave_version,"query: Theo chính sách nghỉ phép hiện hành (2026), nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?",hr_leave_policy,passage: Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.,yes,no,yes,3`

_________________

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Implement thêm 2 scenario `clean` và `inject` vào file `etl_pipeline.py` để khi run với inject sẽ xuất ra 2 database khác nhau dùng để so sánh. Đồng thời thử các phương pháp duplicate thêm, sai policy để làm hỏng dữ liệu.

_________________
