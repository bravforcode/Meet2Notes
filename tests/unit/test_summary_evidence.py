from local_meeting_ai.application.summary_evidence import flag_summary_timestamps, transcript_notes


def test_transcript_notes_surface_exact_original_lines_without_claiming_actions():
    transcript = (
        "[0.0s] Speaker A: ขอ REVIEW budget ก่อน\n"
        "[2.2s] Speaker B: ไม่ต้องส่ง email วันศุกร์\n"
        "[4.0s] Speaker C: รับทราบ"
    )
    notes = transcript_notes(transcript)
    assert "ไม่ใช่สรุป AI" in notes
    assert "ไม่ได้ยืนยันว่าเป็นงาน มติ หรือกำหนดส่ง" in notes
    review, full = notes.split("## Transcript ฉบับเต็ม")
    assert "> [0.0s] Speaker A: ขอ REVIEW budget ก่อน" in review
    assert "> [2.2s] Speaker B: ไม่ต้องส่ง email วันศุกร์" in review
    assert "> [4.0s] Speaker C: รับทราบ" not in review
    assert "\n".join(f"> {line}" for line in transcript.splitlines()) in full


def test_transcript_notes_no_keyword_does_not_claim_there_are_no_tasks():
    notes = transcript_notes("[0.0s] Speaker: เริ่มกันเลย")
    assert "ไม่พบคำค้นที่ตั้งไว้" in notes
    assert "ไม่ได้หมายความว่าไม่มีงาน" in notes
    assert "> [0.0s] Speaker: เริ่มกันเลย" in notes


def test_transcript_notes_limit_only_the_highlights_not_the_full_transcript():
    transcript = "\n".join(f"[{i}.0s] Speaker: ส่งรายงาน {i}" for i in range(35))
    notes = transcript_notes(transcript)
    review, full = notes.split("## Transcript ฉบับเต็ม")
    assert "แสดง 30 จาก 35" in review
    assert "[34.0s] Speaker: ส่งรายงาน 34" not in review
    assert "\n".join(f"> {line}" for line in transcript.splitlines()) in full


def test_transcript_notes_do_not_match_embedded_english_words():
    notes = transcript_notes("[0.0s] Speaker: preprocessing previewer")
    assert "ไม่พบคำค้นที่ตั้งไว้" in notes


def test_reports_unknown_timestamp_and_retains_original_summary():
    text = "## มติ\n- ทดสอบ [12.3s]\n- ส่งรายงาน [88.0s]"
    result, check = flag_summary_timestamps(text, [12300, 13000])
    assert "ไม่พบเวลา [88.0s] ใน transcript ต้นฉบับ" in result
    assert result.endswith(text)
    assert check["checked_count"] == 2
    assert check["unknown_timestamps"] == ["88.0s"]
    assert check["semantic_support_verified"] is False


def test_missing_markers_are_not_treated_as_evidence():
    result, check = flag_summary_timestamps("## สรุป\n- มีการตกลง", [0])
    assert "ไม่พบเวลาอ้างอิง" in result
    assert check["checked_count"] == 0


def test_matching_markers_do_not_claim_semantic_verification():
    result, check = flag_summary_timestamps("## ข้อสรุป\n- ไม่แน่ใจ [0.0s]", [0])
    assert "ตรงกับ transcript" in result
    assert "ไม่ยืนยันว่าข้อความสรุปตรงกับเสียง" in result
    assert check["unknown_timestamps"] == []


def test_summary_service_persists_check_against_canonical_segments():
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from local_meeting_ai.application.ai_services import SummaryService
    from local_meeting_ai.domain.entities import SummaryResult

    segment = SimpleNamespace(
        id=1, segment_index=0, start_ms=12300, end_ms=14000,
        text="Budget สองล้าน", speaker_id=None, confidence=None, metadata={},
    )
    transcriptions = Mock()
    transcriptions.get.return_value = SimpleNamespace(id=2, meeting_id=3, language="th")
    transcriptions.segments.return_value = [segment]
    transcriptions.speakers_for_transcription.return_value = []
    summaries = Mock()
    summaries.get.return_value = SimpleNamespace(template_id=None)
    summaries.complete.return_value = True
    engine = Mock()
    engine.summarize = AsyncMock(return_value=SummaryResult("Budget [88.0s]"))
    plugins = SimpleNamespace(hooks=SimpleNamespace(
        apply_filters=AsyncMock(side_effect=lambda _hook, value, _context: value)
    ))
    preferences = Mock()
    preferences.get_all.return_value = {}
    service = SummaryService(
        engine=engine, summaries=summaries, templates=Mock(),
        transcriptions=transcriptions, jobs=Mock(), preferences=preferences,
        queue=Mock(), plugins=plugins,
    )
    job = SimpleNamespace(uuid="synthetic", payload={
        "summary_id": 4, "transcription_id": 2,
        "summary_template": {"name": "Detailed Thai-English Meeting"},
    })

    asyncio.run(service.process(job, Mock()))
    saved = summaries.complete.call_args.args
    assert "[88.0s]" in saved[1]
    assert saved[2]["derived_artifact"]["timestamp_check"]["unknown_timestamps"] == ["88.0s"]


def test_detailed_notes_fall_back_to_transcript_without_model():
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from local_meeting_ai.application.ai_services import SummaryService

    segment = SimpleNamespace(
        id=1, segment_index=0, start_ms=1200, end_ms=3000,
        text="ขอ review budget ก่อน", speaker_id=None, confidence=None, metadata={},
    )
    transcriptions = Mock()
    transcriptions.get.return_value = SimpleNamespace(
        id=2, meeting_id=3, language="th", status="completed",
    )
    transcriptions.segments.return_value = [segment]
    transcriptions.speakers_for_transcription.return_value = []
    summaries = Mock()
    summaries.create.return_value = SimpleNamespace(id=4)
    summaries.get.return_value = SimpleNamespace(template_id=7)
    summaries.complete.return_value = True
    templates = Mock()
    templates.get.return_value = SimpleNamespace(
        id=7, name="Detailed Thai-English Meeting", system_prompt="",
        user_prompt_template="", sections=[],
    )
    jobs = Mock()
    jobs.create.side_effect = lambda **kwargs: SimpleNamespace(
        uuid="synthetic", payload=kwargs["payload"], cancel_requested=False,
    )
    jobs.get.return_value = SimpleNamespace(cancel_requested=False)
    preferences = Mock()
    preferences.get_all.return_value = {"summary_engine": {"provider": "disabled"}}
    engine = Mock()
    engine.summarize = AsyncMock()
    plugins = SimpleNamespace(hooks=SimpleNamespace(
        apply_filters=AsyncMock(side_effect=lambda _hook, value, _context: value)
    ))
    service = SummaryService(
        engine=engine, summaries=summaries, templates=templates,
        transcriptions=transcriptions, jobs=jobs, preferences=preferences,
        queue=SimpleNamespace(submit=AsyncMock()), plugins=plugins,
    )

    async def run():
        _, job = await service.start(2, template_id=7)
        await service.process(job, Mock())

    asyncio.run(run())
    assert summaries.create.call_args.kwargs["provider"] == "local-extractive"
    output = summaries.complete.call_args.args[1]
    assert "ไม่ใช่สรุป AI" in output
    assert "[1.2s] Unidentified speaker: ขอ review budget ก่อน" in output
    engine.summarize.assert_not_awaited()
