# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Vũ Minh Khải 
**Vai trò:** Monitoring 
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
Tôi phụ trách các phần trong docs:
- data_contract.md
- pipeline_architecture.md
- runbook.md
- quality_report.md

**Kết nối với thành viên khác:**
- Tài liệu trong docs, cần căn cứ vào triển khai thực tế ở các phần của các thành viên khác, như pipeline_architecture.md để hoàn thành,...
- runbook.md ghi lại quá trình xử lý và phát hiện lỗi của 1 case..
_________________

**Bằng chứng (commit / comment trong code):**
commit hash:
a1cda457b36cbe9bc6855810340cfb9abd54f766
69d963ce94cb58c65bb5e2ff80898789eb2d0a57
511b8c1cc729fa26f625a9779f634e43f53b5dec
d3c5768275dba84c0f47d2c4f400e5808dccdc9b
_________________

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

- Thay đổi model embedding mặc định all-MiniLM-L6-v2 bằng intfloat/multilingual-e5-base
Vì model này all-MiniLM-L6-v2 này tuy nhẹ nhưng không hoạt động tốt cho tiếng việt.
Kết quả khi chạy, score trả về của các chunk truy vấn được cao hơn so với dùng all-MiniLM-L6-v2 embedding.
_________________

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.
- Sau khi thay đổi model embedding, kết quả truy vấn cho về score cao hơn cho các chunk nhưng kết quả truy vấn ko tốt lắm... 
- kiểm tra lại phần code về embedding thì thiếu prefix dành cho nội dung trước khi bỏ vào embedding -> bổ sung để fix (model yêu cầu thêm tiền tố passage: và query: trước khi embedding)
_________________

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.
clean,q_refund_window,query: Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,passage: Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày làm việc kể từ xác nhận đơn (ghi chú: bản sync cũ policy-v3 — lỗi migration). [cleaned: stale_refund_window],yes,no,,3
clean,q_p1_sla,query: SLA phản hồi đầu tiên cho ticket P1 là bao lâu?,sla_p1_2026,passage: Ticket P1 có SLA phản hồi ban đầu 15 phút và resolution trong 4 giờ.,yes,no,,3

run_id: cleaned_2026-04-15T10-32Z
_________________

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

_________________
