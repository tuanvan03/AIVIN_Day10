"""
Expectation suite đơn giản (không bắt buộc Great Expectations).

Sinh viên có thể thay bằng GE / pydantic / custom — miễn là có halt có kiểm soát.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    severity: str  # "warn" | "halt"
    detail: str


def run_expectations(cleaned_rows: List[Dict[str, Any]]) -> Tuple[List[ExpectationResult], bool]:
    """
    Trả về (results, should_halt).

    should_halt = True nếu có bất kỳ expectation severity halt nào fail.
    """
    results: List[ExpectationResult] = []

    # E1: có ít nhất 1 dòng sau clean
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # E2: không doc_id rỗng
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    bad_refund = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and "14 ngày làm việc" in (r.get("chunk_text") or "")
    ]
    ok3 = len(bad_refund) == 0
    results.append(
        ExpectationResult(
            "refund_no_stale_14d_window",
            ok3,
            "halt",
            f"violations={len(bad_refund)}",
        )
    )

    # E4: chunk_text đủ dài
    short = [r for r in cleaned_rows if len((r.get("chunk_text") or "")) < 8]
    ok4 = len(short) == 0
    results.append(
        ExpectationResult(
            "chunk_min_length_8",
            ok4,
            "warn",
            f"short_chunks={len(short)}",
        )
    )

    # E5: effective_date đúng định dạng ISO sau clean (phát hiện parser lỏng)
    iso_bad = [
        r
        for r in cleaned_rows
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", (r.get("effective_date") or "").strip())
    ]
    ok5 = len(iso_bad) == 0
    results.append(
        ExpectationResult(
            "effective_date_iso_yyyy_mm_dd",
            ok5,
            "halt",
            f"non_iso_rows={len(iso_bad)}",
        )
    )

    # E6: không còn marker phép năm cũ 10 ngày trên doc HR (conflict version sau clean)
    bad_hr_annual = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and "10 ngày phép năm" in (r.get("chunk_text") or "")
    ]
    ok6 = len(bad_hr_annual) == 0
    results.append(
        ExpectationResult(
            "hr_leave_no_stale_10d_annual",
            ok6,
            "halt",
            f"violations={len(bad_hr_annual)}",
        )
    )

    # E7: Không có chứa thông tin nhạy cảm (Số điện thoại)
    bad_pii = [
        r
        for r in cleaned_rows
        if re.search(r"\b0[1-9]\d{8}\b", r.get("chunk_text") or "")
    ]
    ok7 = len(bad_pii) == 0
    results.append(
        ExpectationResult(
            "no_pii_phone_numbers",
            ok7,
            "halt",
            f"violations={len(bad_pii)}",
        )
    )

    # E8: Phải fix hoàn toàn lỗi SLA '12 hours'
    bad_sla = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "sla_p1_2026"
        and "12 hours" in (r.get("chunk_text") or "")
    ]
    ok8 = len(bad_sla) == 0
    results.append(
        ExpectationResult(
            "sla_no_stale_12_hours",
            ok8,
            "halt",
            f"violations={len(bad_sla)}",
        )
    )

    halt = any(not r.passed and r.severity == "halt" for r in results)
    return results, halt


if __name__ == "__main__":
    # Khởi tạo 30 testcases với các tình huống đa dạng thử nghiệm Rule Expectations
    test_rows_sprint2 = [
        # --- VALID CASES (Pass Expectations) ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Tài liệu hdsd portal IT Helpdesk 2026.", "effective_date": "2026-03-01", "exported_at": "2026-04-10T08:00:00"}, # 1
        {"doc_id": "hr_leave_policy", "chunk_text": "Qui định nghỉ phép năm 2026 là 15 ngày.", "effective_date": "2026-02-15", "exported_at": "2026-04-10T08:00:00"}, # 2
        {"doc_id": "sla_p1_2026", "chunk_text": "SLA P1 luôn phải được đáp ứng trong 4 hours.", "effective_date": "2026-02-15", "exported_at": "2026-04-10"}, # 3
        
        # --- E2 Violations (no_empty_doc_id) ---
        {"doc_id": "", "chunk_text": "Không có doc id", "effective_date": "2026-01-01"}, # 4
        {"doc_id": "   ", "chunk_text": "Khoảng trắng doc_id", "effective_date": "2026-01-01"}, # 5
        
        # --- E3 Violations (refund_no_stale_14d_window) ---
        {"doc_id": "policy_refund_v4", "chunk_text": "14 ngày làm việc", "effective_date": "2026-02-01"}, # 6
        {"doc_id": "policy_refund_v4", "chunk_text": "Gửi trong vòng 14 ngày làm việc.", "effective_date": "2026-02-01"}, # 7
        
        # --- E4 Violations (chunk_min_length_8) - warn ---
        {"doc_id": "sla_p1_2026", "chunk_text": "Ngắn", "effective_date": "2026-01-01"}, # 8
        {"doc_id": "hr_leave_policy", "chunk_text": "1234567", "effective_date": "2026-01-01"}, # 9
        
        # --- E5 Violations (effective_date_iso_yyyy_mm_dd) ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "FAQ test invalid date format 1", "effective_date": "26-02"}, # 10
        {"doc_id": "sla_p1_2026", "chunk_text": "Test date format fail 2", "effective_date": "01/01/2026"}, # 11
        {"doc_id": "it_helpdesk_faq", "chunk_text": "FAQ test empty date format", "effective_date": ""}, # 12
        
        # --- E6 Violations (hr_leave_no_stale_10d_annual) ---
        {"doc_id": "hr_leave_policy", "chunk_text": "Quy định 10 ngày phép năm cũ nha", "effective_date": "2026-01-01"}, # 13
        {"doc_id": "hr_leave_policy", "chunk_text": "Tôi được 10 ngày phép năm.", "effective_date": "2026-01-01"}, # 14
        
        # --- E7: NEW RULE Violations (no_pii_phone_numbers) ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Gọi số 0912345678 liền đi.", "effective_date": "2026-01-01"}, # 15
        {"doc_id": "policy_refund_v4", "chunk_text": "Liên hệ ngay bác Vinh theo số điện thoại 0987654321.", "effective_date": "2026-01-01"}, # 16
        {"doc_id": "sla_p1_2026", "chunk_text": "0123456789 đang bảo trì do lỗi mạng diện rộng.", "effective_date": "2026-01-01"}, # 17
        {"doc_id": "hr_leave_policy", "chunk_text": "Lộ số PII phone = 0933334444 nhé", "effective_date": "2026-01-01"}, # 18
        
        # --- E8: NEW RULE Violations (sla_no_stale_12_hours) ---
        {"doc_id": "sla_p1_2026", "chunk_text": "Ticket P1 có thời gian giải quyết là 12 hours theo quy định.", "effective_date": "2026-01-01"}, # 19
        {"doc_id": "sla_p1_2026", "chunk_text": "Yêu cầu khắt khe không được vượt quá 12 hours timeout.", "effective_date": "2026-01-01"}, # 20
        
        # --- ADDITIONAL MIXTURES AND VALIDS ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Mật khẩu của bạn là abcxyz", "effective_date": "2026-01-01"}, # 21
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Portal update hàng tuần nha", "effective_date": "2026-01-01"}, # 22
        {"doc_id": "policy_refund_v4", "chunk_text": "Đổi mật khẩu theo FAQ không phải refund.", "effective_date": "2026-02-01"}, # 23
        {"doc_id": "sla_p1_2026", "chunk_text": "Ticket giải quyết nhanh gọn", "effective_date": "2026-01-01"}, # 24
        {"doc_id": "hr_leave_policy", "chunk_text": "Không được nghỉ quá mức nha", "effective_date": "2026-01-01"}, # 25
        {"doc_id": "policy_refund_v4", "chunk_text": "Refund tối đa trong 7 ngày làm việc", "effective_date": "2026-01-01"}, # 26
        {"doc_id": "policy_refund_v4", "chunk_text": "Quy trình xác nhận", "effective_date": "2026-01-01"}, # 27
        {"doc_id": "sla_p1_2026", "chunk_text": "Test sla length limit OK", "effective_date": "2026-01-01"}, # 28
        {"doc_id": "hr_leave_policy", "chunk_text": "Thông báo HR năm 2026 chốt 12 ngày.", "effective_date": "2026-05-01"}, # 29
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Câu hỏi số 30 hoàn thành", "effective_date": "2026-10-10"} # 30
    ]

    print(f"\n--- [CHẠY TEST SUITE EXPECTATION SPRINT 2: {len(test_rows_sprint2)} RECORD ĐẦU VÀO] ---")
    results, halt = run_expectations(test_rows_sprint2)
    
    print(f"\n>> EXPECTATIONS RAN: {len(results)}")
    for r in results:
        status = "PASSED" if r.passed else "FAILED"
        print(f"[{status}] {r.name} (severity: {r.severity}) -> {r.detail}")
        
    print(f"\n>> PIPELINE HALT TRIGGERED? : {halt}")
    assert halt is True, "Pipeline expected to halt due to intentionally embedded bad records!"
    print("\n[+] TEST CASES CHO EXPECTATION ĐÃ CHẠY HOÀN TẤT!")
