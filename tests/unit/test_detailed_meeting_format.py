from local_meeting_ai.adapters.summary.llama_cpp import LlamaCppSummaryEngine
from local_meeting_ai.application.summary_templates import BUILTIN_SUMMARY_TEMPLATES
from local_meeting_ai.plugins.contracts import MeetingDocument, TranscriptDocumentSegment


def test_detailed_format_reaches_summary_prompt_with_timestamped_transcript():
    template = next(
        item for item in BUILTIN_SUMMARY_TEMPLATES
        if item["name"] == "Detailed Thai-English Meeting"
    )
    prompt, system = LlamaCppSummaryEngine._summary_instructions(
        {"summary_template": template, "response_language": "th"}
    )
    document = MeetingDocument(
        meeting_id=1,
        transcription_id=2,
        segments=[TranscriptDocumentSegment(
            id=3, index=0, start_ms=123400, end_ms=125000,
            text="ส่ง report วันศุกร์", speaker_id=None, speaker_label="Speaker 1",
        )],
    )
    assert document.prompt_text() == "[123.4s] Speaker 1: ส่ง report วันศุกร์"
    assert "Copy exact transcript timestamps" in prompt
    assert "never invent citations" in prompt
    assert "Not specified" in prompt
    assert "## ข้อมูลที่ต้องตรวจสอบ" in prompt
    assert "do not prove a person's identity" in system
    assert document.segments[0].text == "ส่ง report วันศุกร์"
