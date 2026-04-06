"""Tests for domain models and Pydantic schemas."""

import pytest

from packages.common.response import ApiResponse, PagedData, TaskAccepted
from packages.domain.documents import (
    CreativeBriefDocument,
    ScriptDocument,
    ScriptSection,
    StoryboardDocument,
    TimelineDocument,
)


class TestApiResponse:
    def test_default_response(self):
        resp = ApiResponse(data={"key": "value"})
        assert resp.code == 0
        assert resp.message == "ok"
        assert resp.data == {"key": "value"}
        assert resp.request_id.startswith("req_")

    def test_paged_data(self):
        paged = PagedData(items=[1, 2, 3], total=100, page=1, page_size=20)
        assert len(paged.items) == 3
        assert paged.total == 100

    def test_task_accepted(self):
        task = TaskAccepted(task_id="task_123")
        assert task.status == "queued"


class TestCreativeBriefDocument:
    def test_create_brief(self):
        brief = CreativeBriefDocument(
            project_id=1001,
            version_no=1,
        )
        assert brief.project_id == 1001
        assert brief.structured_brief.duration_sec == 30
        assert brief.structured_brief.aspect_ratio == "16:9"

    def test_brief_with_constraints(self):
        brief = CreativeBriefDocument(
            project_id=1001,
            version_no=1,
        )
        brief.constraints.must_include = ["Logo"]
        brief.constraints.max_duration_sec = 60
        assert "Logo" in brief.constraints.must_include


class TestScriptDocument:
    def test_create_script(self):
        script = ScriptDocument(
            project_id=1001,
            version_no=1,
            title="Test Script",
            sections=[
                ScriptSection(
                    section_no=1,
                    title="Opening",
                    narration="Night falls",
                )
            ],
        )
        assert script.title == "Test Script"
        assert len(script.sections) == 1
        assert script.sections[0].narration == "Night falls"


class TestStoryboardDocument:
    def test_create_storyboard(self):
        sb = StoryboardDocument(project_id=1001)
        assert sb.scenes == []
        assert sb.version_no == 1


class TestTimelineDocument:
    def test_create_timeline(self):
        tl = TimelineDocument(project_id=1001)
        assert tl.tracks == []
        assert tl.subtitle_segments == []
        assert tl.transitions == []
