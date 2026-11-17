from __future__ import annotations

import time

from local_meeting_ai.domain.entities import SegmentDraft
from local_meeting_ai.domain.enums import SourceType


def test_detailed_summary_api_without_model_uses_synthetic_transcript(client):
    container = client.app.state.container
    meeting = container.meetings.create(
        title="Synthetic meeting", description=None, source_type=SourceType.MANUAL,
        language="th",
    )
    transcript = container.transcriptions.create(
        meeting_id=meeting.id, title="Synthetic", engine="synthetic", model="none",
        language="th", settings={},
    )
    container.transcriptions.complete(transcript.id, language="th", segments=[
        SegmentDraft(index=0, start_ms=0, end_ms=2000, text="ขอ review budget ก่อน"),
        SegmentDraft(index=1, start_ms=2200, end_ms=4000, text="ตกลง คุยกับ vendor วันศุกร์"),
    ])
    response = client.put("/api/settings", json={"summary_engine": {"provider": "disabled"}})
    assert response.status_code == 200
    template = next(
        item for item in client.get("/api/summary-templates").json()
        if item["name"] == "Detailed Thai-English Meeting"
    )
    started = client.post(
        f"/api/transcriptions/{transcript.id}/summaries", json={"template_id": template["id"]},
    )
    assert started.status_code == 202, started.text
    for _ in range(100):
        job = client.get(f"/api/jobs/{started.json()['job']['uuid']}").json()
        if job["status"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.02)
    assert job["status"] == "completed", job
    summary = client.get(f"/api/summaries/{started.json()['summary']['id']}").json()
    assert summary["provider"] == "local-extractive"
    assert "ไม่ใช่สรุป AI" in summary["content_markdown"]
    review, full = summary["content_markdown"].split("## Transcript ฉบับเต็ม")
    assert "[0.0s] Unidentified speaker: ขอ review budget ก่อน" in review
    assert "[2.2s] Unidentified speaker: ตกลง คุยกับ vendor วันศุกร์" in review
    assert "[0.0s] Unidentified speaker: ขอ review budget ก่อน" in full
    assert "[0.0s] Unidentified speaker: ขอ review budget ก่อน" in summary["content_markdown"]
    assert "[2.2s] Unidentified speaker: ตกลง คุยกับ vendor วันศุกร์" in summary["content_markdown"]
