# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Ninh Quang Trí <br>
**Vai trò:** Embed  <br>
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

`eval_rerieval.py`, `grading_run.py`, `etl_pipeline.py`, `artifacts/`

**Kết nối với thành viên khác:**

Bổ sung scenario vào file `etl_pipeline.py` của Tuấn để xuất ra csv, chia 2 database tương ứng với 2 scenatio clean và inject, thêm option chọn database dựa theo scenario vào `eval_rerieval.py`, `grading_run.py`.

**Bằng chứng (commit / comment trong code):**

`a36ded0049c7ab0e45f00683a82303f8cbcbd8e4`, `1c2ab3cfa5590c29cbe7152e686badde049a780e`, `2087a9ed53f44d3b454a79c96d2a63e11050266c`, `cb81c214add277df043378f9ea9f704dc209f541`, `ae6853fbc5daa08a741af216a93fbfab9b4b48d3`, `13d15435651e05a73a176e84f224ccd13f94d771`,
`67ad1e641bd949dffaf798a82a93287284109d30`, `6f39cf229024407063f25709184f494f761040cc`

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> Chọn 2 option cho scenario là `clean` và `inject` và thay đổi file `etl_pipeline.py` để khi run với inject và clean thì sẽ xuất ra các file eval, logs, manifests, quarantine để so sánh đồng thời chia thành 2 database riêng biệt để tránh các kết quả giống nhau trong cả 2 scenario.

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

> Thử implement các phương pháp duplicate thêm, sai policy để làm hỏng dữ liệu.

_________________
