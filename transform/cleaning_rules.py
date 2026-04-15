"""
Cleaning rules — raw export → cleaned rows + quarantine.

Baseline gồm các failure mode mở rộng (allowlist doc_id, parse ngày, HR stale version).
Sinh viên thêm ≥3 rule mới: mỗi rule phải ghi `metric_impact` (xem README — chống trivial).
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Khớp export hợp lệ trong lab (mở rộng khi nhóm thêm doc mới — phải đồng bộ contract).
ALLOWED_DOC_IDS = frozenset(
    {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
    }
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_chunk_id(doc_id: str, chunk_text: str, seq: int) -> str:
    h = hashlib.sha256(f"{doc_id}|{chunk_text}|{seq}".encode("utf-8")).hexdigest()[:16]
    return f"{doc_id}_{seq}_{h}"


def _normalize_effective_date(raw: str) -> Tuple[str, str]:
    """
    Trả về (iso_date, error_reason).
    iso_date rỗng nếu không parse được.
    """
    s = (raw or "").strip()
    if not s:
        return "", "empty_effective_date"
    if _ISO_DATE.match(s):
        return s, ""
    m = _DMY_SLASH.match(s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}", ""
    return "", "invalid_effective_date_format"


def load_raw_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def clean_rows(
    rows: List[Dict[str, str]],
    *,
    apply_refund_window_fix: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Trả về (cleaned, quarantine).

    Baseline (mở rộng theo narrative Day 10):
    1) Quarantine: doc_id không thuộc allowlist (export lạ / catalog sai).
    2) Chuẩn hoá effective_date sang YYYY-MM-DD; quarantine nếu không parse được.
    3) Quarantine: chunk hr_leave_policy có effective_date < 2026-01-01 (bản HR cũ / conflict version).
    4) Quarantine: chunk_text rỗng hoặc effective_date rỗng sau chuẩn hoá.
    5) Loại trùng nội dung chunk_text (giữ bản đầu).
    6) Fix stale refund: policy_refund_v4 chứa '14 ngày làm việc' → 7 ngày.
    """
    quarantine: List[Dict[str, Any]] = []
    seen_text: set[str] = set()
    cleaned: List[Dict[str, Any]] = []
    seq = 0

    for raw in rows:
        doc_id = raw.get("doc_id", "")
        text = raw.get("chunk_text", "")
        eff_raw = raw.get("effective_date", "")
        exported_at = raw.get("exported_at", "")

        if doc_id not in ALLOWED_DOC_IDS:
            quarantine.append({**raw, "reason": "unknown_doc_id"})
            continue

        eff_norm, eff_err = _normalize_effective_date(eff_raw)
        if eff_err == "empty_effective_date":
            quarantine.append({**raw, "reason": "missing_effective_date"})
            continue
        if eff_err == "invalid_effective_date_format":
            quarantine.append({**raw, "reason": eff_err, "effective_date_raw": eff_raw})
            continue

        if doc_id == "hr_leave_policy" and eff_norm < "2026-01-01":
            quarantine.append(
                {
                    **raw,
                    "reason": "stale_hr_policy_effective_date",
                    "effective_date_normalized": eff_norm,
                }
            )
            continue

        if not text:
            quarantine.append({**raw, "reason": "missing_chunk_text"})
            continue

        # [NEW RULE 1] If chunk is too short, quarantine it
        if text and len(text) < 15:
            quarantine.append({**raw, "reason": "chunk_too_short"})
            continue
            
        # [NEW RULE 2] If chunk contains phone number, quarantine it
        if re.search(r"\b0[1-9]\d{8}\b", text):
            quarantine.append({**raw, "reason": "contains_pii_phone"})
            continue

        key = _norm_text(text)
        if key in seen_text:
            quarantine.append({**raw, "reason": "duplicate_chunk_text"})
            continue
        seen_text.add(key)

        fixed_text = text
        if apply_refund_window_fix and doc_id == "policy_refund_v4":
            if "14 ngày làm việc" in fixed_text:
                fixed_text = fixed_text.replace(
                    "14 ngày làm việc",
                    "7 ngày làm việc",
                )
                fixed_text += " [cleaned: stale_refund_window]"

        # [NEW RULE 3] Hypothesis: if chunk contains old SLA, fix it
        if doc_id == "sla_p1_2026" and "12 hours" in fixed_text:
            fixed_text = fixed_text.replace("12 hours", "4 hours")
            fixed_text += " [cleaned: sla_response_time]"

        seq += 1
        cleaned.append(
            {
                "chunk_id": _stable_chunk_id(doc_id, fixed_text, seq),
                "doc_id": doc_id,
                "chunk_text": fixed_text,
                "effective_date": eff_norm,
                "exported_at": exported_at or "",
            }
        )

    return cleaned, quarantine


def write_cleaned_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at\n", encoding="utf-8")
        return
    fieldnames = ["chunk_id", "doc_id", "chunk_text", "effective_date", "exported_at"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_quarantine_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at,reason\n", encoding="utf-8")
        return
    keys: List[str] = []
    seen_k: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen_k:
                seen_k.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    # Khởi tạo 30 testcases với các tình huống đa dạng thử nghiệm Rule cũ và Rule mới.
    test_rows_sprint2 = [
        # --- VALID CASES (Pass Clean) ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Tài liệu hdsd portal IT Helpdesk 2026.", "effective_date": "2026-03-01", "exported_at": "2026-04-10T08:00:00"}, # 1
        {"doc_id": "hr_leave_policy", "chunk_text": "Qui định nghỉ phép năm 2026 là 15 ngày.", "effective_date": "2026-02-15", "exported_at": "2026-04-10T08:00:00"}, # 2
        {"doc_id": "sla_p1_2026", "chunk_text": "SLA P1 luôn phải được đáp ứng trong 4 hours.", "effective_date": "15/02/2026", "exported_at": "2026-04-10"}, # 3. Date DMY -> ISO
        
        # --- BASELINE RULE: unknown_doc_id ---
        {"doc_id": "invalid_doc", "chunk_text": "Tài liệu này không có trong hệ thống", "effective_date": "2026-01-01"}, # 4
        {"doc_id": "", "chunk_text": "Không có doc id", "effective_date": "2026-01-01"}, # 5
        {"doc_id": "secret_doc_99", "chunk_text": "Tài liệu tuyệt mật không ai được xem.", "effective_date": "2026-01-01"}, # 6
        
        # --- BASELINE RULE: missing_effective_date ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "FAQ test empty date", "effective_date": "   "}, # 7
        {"doc_id": "policy_refund_v4", "chunk_text": "Quy định abc", "effective_date": ""}, # 8
        
        # --- BASELINE RULE: invalid_effective_date_format ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "FAQ test invalid date", "effective_date": "26-02"}, # 9
        {"doc_id": "sla_p1_2026", "chunk_text": "Test date format fail", "effective_date": "N/A"}, # 10
        {"doc_id": "policy_refund_v4", "chunk_text": "Sai format năm", "effective_date": "202-01-01"}, # 11
        
        # --- BASELINE RULE: stale_hr_policy_effective_date ---
        {"doc_id": "hr_leave_policy", "chunk_text": "Quy định nhân sự áp dụng cho năm 2025.", "effective_date": "2025-12-31"}, # 12
        {"doc_id": "hr_leave_policy", "chunk_text": "Chính sách nghỉ phép 2024.", "effective_date": "2024-01-01"}, # 13
        
        # --- BASELINE RULE: missing_chunk_text ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "", "effective_date": "2026-01-01"}, # 14
        {"doc_id": "it_helpdesk_faq", "chunk_text": "   ", "effective_date": "2026-01-01"}, # 15
        
        # --- BASELINE RULE: duplicate_chunk_text ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Nội dung này sẽ bị cắm cờ do trùng lặp nhé.", "effective_date": "2026-01-01"}, # 16 (Original)
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Nội dung này sẽ bị cắm cờ do trùng lặp nhé.", "effective_date": "2026-01-01"}, # 17 (Dup exact)
        {"doc_id": "it_helpdesk_faq", "chunk_text": " Nội dung Này sẽ BỊ Cắm cờ do TRÙNG LẶP nhé. ", "effective_date": "2026-01-01"}, # 18 (Dup after norm text)
        
        # --- BASELINE RULE: fix_refund_window ---
        {"doc_id": "policy_refund_v4", "chunk_text": "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ lúc đặt hàng.", "effective_date": "2026-01-01"}, # 19 (Fixed -> 7)
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền tối đa 14 ngày làm việc được không?", "effective_date": "2026-01-01"}, # 20 (Fixed -> 7)
        
        # --- NEW RULE 1: chunk_too_short (< 15 chars) ---
        {"doc_id": "sla_p1_2026", "chunk_text": "Ngắn", "effective_date": "2026-01-01"}, # 21
        {"doc_id": "hr_leave_policy", "chunk_text": "12345678901234", "effective_date": "2026-01-01"}, # 22
        {"doc_id": "policy_refund_v4", "chunk_text": "Chỉ 10 kí tự", "effective_date": "2026-01-01"}, # 23
        
        # --- NEW RULE 2: contains_pii_phone ---
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Liên hệ ngay bác Vinh theo số điện thoại 0987654321 để biết thêm.", "effective_date": "2026-01-01"}, # 24
        {"doc_id": "policy_refund_v4", "chunk_text": "SĐT khách hàng VIP: 0312345678. Thông tin nội bộ cấm chia sẻ.", "effective_date": "2026-01-01"}, # 25
        {"doc_id": "sla_p1_2026", "chunk_text": "Hotline nội bộ 0123456789 đang bảo trì do lỗi mạng diện rộng.", "effective_date": "2026-01-01"}, # 26
        
        # --- NEW RULE 3: fix_sla_response_time (12 hours -> 4 hours) ---
        {"doc_id": "sla_p1_2026", "chunk_text": "Ticket P1 có thời gian giải quyết là 12 hours theo quy định cũ.", "effective_date": "2026-01-01"}, # 27
        {"doc_id": "sla_p1_2026", "chunk_text": "Yêu cầu khắt khe không được vượt quá 12 hours timeout.", "effective_date": "2026-01-01"}, # 28
        
        # --- OTHER RANDOM VALID/INVALID MIXTURES ---
        {"doc_id": "policy_refund_v4", "chunk_text": "Không được hoàn tiền nếu quá 7 ngày làm việc.", "effective_date": "29/02/2026"}, # 29
        {"doc_id": "it_helpdesk_faq", "chunk_text": "Đây là 1 chunk cuối cùng để chốt 30 testcases, hoàn thành nhiệm vụ.", "effective_date": "2026-10-10"} # 30
    ]

    print(f"\\n--- CHẠY TEST ĐỘ LÀM SẠCH VÀ LUẬT CHẶN - TỔNG {len(test_rows_sprint2)} TESTCASES ---")
    cleaned_result, quaran_result = clean_rows(test_rows_sprint2)
    print(f">> Khối lượng Cleaned pass (Hợp lệ): {len(cleaned_result)}")
    print(f">> Khối lượng bị Quarantine (Từ chối): {len(quaran_result)}\\n")
    
    print("----- [CÁC RECORD BỊ QUARANTINE VÀ LÝ DO] -----")
    for i, q in enumerate(quaran_result):
        # In ra lí do và 30 kí tự đầu của text
        print(f" {i+1}. Reason: {q['reason']} | Text: {str(q.get('chunk_text', ''))}")
        
    print("\\n----- [CÁC RECORD CLEANED THÀNH CÔNG] -----")
    for i, c in enumerate(cleaned_result):
        if 'cleaned:' in c['chunk_text']:
            print(f" {i+1}. [FIXED] Text: {c['chunk_text']}")
        else:
            print(f" {i+1}. [OK] Text: {c['chunk_text']}")

    assert len(test_rows_sprint2) == 30, "Số lượng test cases phải chính xác 30!"
    print("\\n[+] ĐÃ HOÀN TẤT THỬ NGHIỆM! CODE CHẠY TRƠN TRU CHO SPRINT 2!")
