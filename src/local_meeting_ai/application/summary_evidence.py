"""Check timestamp markers in one generated summary against its source transcript."""

from __future__ import annotations

import re
from collections.abc import Iterable

_TIMESTAMP = re.compile(r"\[(\d+\.\ds)\]")
_REVIEW_TERMS = re.compile(
    r"ส่ง|นัด|กำหนด|พรุ่งนี้|มะรืน|วันนี้|วันจันทร์|วันอังคาร|วันพุธ|วันพฤหัส|"
    r"วันศุกร์|วันเสาร์|วันอาทิตย์|โมง|"
    r"(?<![a-z])(?:report|email|review|deadline|due|follow[ -]?up|send)(?![a-z])",
    re.IGNORECASE,
)
_REVIEW_LIMIT = 30


def transcript_notes(transcript: str) -> str:
    """Return the transcript as evidence, without inferring a meeting summary."""
    lines = transcript.splitlines()
    quoted = "\n".join(f"> {line}" for line in lines)
    candidates = [line for line in lines if _REVIEW_TERMS.search(line)]
    if candidates:
        highlights = "\n".join(f"> {line}" for line in candidates[:_REVIEW_LIMIT])
        if len(candidates) > _REVIEW_LIMIT:
            highlights += (
                f"\n\nแสดง {_REVIEW_LIMIT} จาก {len(candidates)} บรรทัดที่พบคำค้น "
                "โดย transcript ฉบับเต็มอยู่ด้านล่าง"
            )
    else:
        highlights = "ไม่พบคำค้นที่ตั้งไว้ ทั้งนี้ไม่ได้หมายความว่าไม่มีงานหรือกำหนดเวลา"
    return (
        "# บันทึกจาก transcript\n\n"
        "**โหมดข้อความต้นฉบับ:** ยังไม่มีโมเดลสรุปพร้อมใช้งาน "
        "เนื้อหาด้านล่างเป็น transcript ตามลำดับ ไม่ใช่สรุป AI "
        "และไม่ได้สกัดมติ งาน ผู้รับผิดชอบ หรือกำหนดส่ง โปรดตรวจเทียบกับเสียง\n\n"
        "## ข้อความที่ควรตรวจ\n\n"
        "คัดบรรทัดต้นฉบับด้วยคำค้นเบื้องต้นเท่านั้น "
        "ไม่ได้ยืนยันว่าเป็นงาน มติ หรือกำหนดส่ง และอาจตกหล่นข้อความสำคัญ\n\n"
        f"{highlights}\n\n"
        "## Transcript ฉบับเต็ม\n\n"
        f"{quoted}\n"
    )


def flag_summary_timestamps(
    content: str, source_start_ms: Iterable[int]
) -> tuple[str, dict[str, object]]:
    """Flag unknown markers; matching times do not establish factual support."""
    source = {f"{start / 1000:.1f}s" for start in source_start_ms}
    markers = _TIMESTAMP.findall(content)
    unknown = sorted(set(markers) - source)

    if unknown:
        detail = (
            "ไม่พบเวลา " + ", ".join(f"[{marker}]" for marker in unknown)
            + " ใน transcript ต้นฉบับ"
        )
    elif not markers:
        detail = "ไม่พบเวลาอ้างอิงในรูปแบบ [วินาที.ทศนิยมหนึ่งตำแหน่งs]"
    else:
        detail = "เวลาอ้างอิงในรูปแบบ [วินาที.ทศนิยมหนึ่งตำแหน่งs] ตรงกับ transcript"

    warning = (
        f"> **ตรวจสอบสรุป:** {detail} การตรวจนี้ไม่ยืนยันว่าข้อความสรุปตรงกับเสียง "
        "และไม่ตรวจเวลาที่เขียนรูปแบบอื่น โปรดเปิดฟังและตรวจชื่อ ตัวเลข มติ และงานที่มอบหมาย\n\n"
    )
    return warning + content, {
        "format": "[seconds.one_decimal_s]",
        "checked_count": len(markers),
        "unknown_timestamps": unknown,
        "semantic_support_verified": False,
    }
