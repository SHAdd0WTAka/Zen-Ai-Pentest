import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from core.template_engine import (
    Extractor,
    ExtractorType,
    Matcher,
    MatcherType,
    TemplateDefinition,
    TemplateEngine,
    TemplateInfo,
    TemplateRequest,
    TemplateResult,
    WorkflowDefinition,
    WorkflowStep,
    _parse_extractor,
    _parse_matcher,
    _parse_request,
    _parse_template,
    _parse_workflow,
    _resolve_json_path,
)


class TestMatcher:
    def test_status_matcher_matching(self):
        m = Matcher(type=MatcherType.STATUS, status=[200, 301])
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        assert engine._match_status(m, 200) is True
        assert engine._match_status(m, 404) is False

    def test_word_matcher_or_condition(self):
        m = Matcher(type=MatcherType.WORD, words=["admin", "login"], condition="or")
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        assert engine._match_words(m, "admin panel") is True
        assert engine._match_words(m, "welcome") is False

    def test_word_matcher_and_condition(self):
        m = Matcher(type=MatcherType.WORD, words=["admin", "login"], condition="and")
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        assert engine._match_words(m, "admin login page") is True
        assert engine._match_words(m, "admin only") is False

    def test_regex_matcher_matching(self):
        m = Matcher(type=MatcherType.REGEX, regex=[r"CVE-\d{4}-\d+", r"admin"])
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        assert engine._match_regex(m, "Found CVE-2024-1234") is True
        assert engine._match_regex(m, "nothing here") is False

    def test_empty_matchers_return_false(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        matched, reason = engine._evaluate_matchers([], 200, "body")
        assert matched is False
        assert reason == ""


class TestExtractor:
    def test_regex_extractor(self):
        ext = Extractor(type=ExtractorType.REGEX, name="cve_id", regex=[r"CVE-\d{4}-\d+"])
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        result = engine._execute_extractors([ext], "CVE-2024-1234", {})
        assert result["cve_id"] == "CVE-2024-1234"

    def test_json_extractor(self):
        ext = Extractor(type=ExtractorType.JSON, name="version", json=["version"])
        body = json.dumps({"version": "1.2.3", "name": "test"})
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        result = engine._execute_extractors([ext], body, {})
        assert result["version"] == "1.2.3"

    def test_json_path_resolution(self):
        data = {"a": {"b": [{"c": "found"}]}}
        assert _resolve_json_path(data, "a.b") == [{"c": "found"}]
        assert _resolve_json_path(data, "a.b.0.c") == "found"
        assert _resolve_json_path(data, "missing") is None

    def test_extractor_unnamed_values(self):
        ext = Extractor(type=ExtractorType.REGEX, regex=[r"\d{3}"])
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        result = engine._execute_extractors([ext], "code 123 and 456", {})
        assert result["value_0"] == "123"
        assert result["value_1"] == "456"


class TestTemplateDefinition:
    def test_parse_from_dict(self):
        data = {
            "id": "test-template",
            "info": {"name": "Test", "severity": "high", "author": "tester"},
            "requests": [{"method": "GET", "path": "/"}],
        }
        t = _parse_template(data)
        assert t.id == "test-template"
        assert t.info.name == "Test"
        assert t.info.severity.value == "high"
        assert len(t.requests) == 1

    def test_parse_with_matchers_and_extractors(self):
        data = {
            "id": "full-template",
            "info": {"name": "Full", "severity": "critical"},
            "requests": [
                {
                    "method": "POST",
                    "path": "/api/login",
                    "body": '{"user":"admin"}',
                    "matchers": [
                        {"type": "status", "status": [200]},
                        {"type": "word", "words": ["token"], "condition": "and"},
                    ],
                    "extractors": [
                        {"type": "regex", "name": "token", "regex": [r"token:\s*(\S+)"]},
                    ],
                }
            ],
        }
        t = _parse_template(data)
        req = t.requests[0]
        assert req.method == "POST"
        assert req.body == '{"user":"admin"}'
        assert len(req.matchers) == 2
        assert len(req.extractors) == 1
        assert req.extractors[0].name == "token"

    def test_parse_matcher(self):
        m = _parse_matcher({"type": "status", "status": [200, 404], "condition": "or"})
        assert m.type == MatcherType.STATUS
        assert m.status == [200, 404]
        assert m.condition == "or"

    def test_parse_extractor(self):
        e = _parse_extractor({"type": "json", "name": "version", "json": ["version"]})
        assert e.type == ExtractorType.JSON
        assert e.name == "version"
        assert e.json == ["version"]

    def test_parse_request_defaults(self):
        r = _parse_request({})
        assert r.method == "GET"
        assert r.path == ["/"]
        assert r.matchers == []
        assert r.extractors == []

    def test_template_result_to_dict(self):
        r = TemplateResult(
            template_id="t1",
            template_name="Test",
            matched=True,
            matched_reason="status 200",
            extracted={"key": "val"},
            status_code=200,
            url="http://test.com",
            execution_time=0.5,
        )
        d = r.to_dict()
        assert d["template_id"] == "t1"
        assert d["matched"] is True
        assert d["extracted"]["key"] == "val"


class TestWorkflowDefinition:
    def test_parse_workflow(self):
        data = {
            "id": "test-workflow",
            "info": {"name": "WF", "severity": "info"},
            "workflows": [
                {"template": "tech/", "matchers": [{"condition": "or"}]},
                {"template": "custom/test", "matchers": [{"condition": "and"}]},
            ],
        }
        wf = _parse_workflow(data)
        assert wf.id == "test-workflow"
        assert len(wf.steps) == 2
        assert wf.steps[0].template_ref == "tech/"
        assert wf.steps[0].condition == "or"
        assert wf.steps[1].condition == "and"


class TestTemplateEngineLoading:
    def test_load_template_from_yaml_file(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"id": "file-template", "info": {"name": "File Template"}, "requests": [{"method": "GET"}]}, f)
            fpath = Path(f.name)
        try:
            t = engine.load_template(fpath)
            assert t is not None
            assert t.id == "file-template"
            assert t.info.name == "File Template"
        finally:
            fpath.unlink(missing_ok=True)

    def test_load_workflow_from_yaml_file(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"id": "wf-test", "info": {"name": "WF"}, "workflows": [{"template": "test/"}]}, f)
            fpath = Path(f.name)
        try:
            wf = engine.load_workflow(fpath)
            assert wf is not None
            assert wf.id == "wf-test"
            assert len(wf.steps) == 1
        finally:
            fpath.unlink(missing_ok=True)

    def test_load_bad_yaml_returns_none(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("{{{invalid: yaml: []]]}")
            fpath = Path(f.name)
        try:
            result = engine.load_template(fpath)
            assert result is None
        finally:
            fpath.unlink(missing_ok=True)

    def test_load_missing_file_returns_none(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        assert engine.load_template(Path("/nonexistent/file.yaml")) is None

    def test_resolve_template_ref_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tdir = Path(tmpdir)
            (tdir / "tests").mkdir(parents=True)
            t1 = tdir / "tests" / "alpha.yaml"
            t2 = tdir / "tests" / "beta.yaml"
            for p in (t1, t2):
                yaml.dump({"id": p.stem, "info": {"name": p.stem}, "requests": []}, p.open("w"))
            engine = TemplateEngine(templates_dir=tdir)
            templates = engine.resolve_template_ref("tests/")
            assert len(templates) == 2

    def test_list_templates_and_workflows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tdir = Path(tmpdir)
            (tdir / "workflows").mkdir(parents=True)
            (tdir / "test.yaml").write_text("id: tpl\ninfo: {name: T}\nrequests: []")
            (tdir / "workflows" / "wf.yaml").write_text("id: wf\ninfo: {name: W}\nworkflows: []")
            engine = TemplateEngine(templates_dir=tdir)
            templates = engine.list_templates()
            workflows = engine.list_workflows()
            assert len(templates) >= 1
            assert len(workflows) == 1

    @pytest.mark.asyncio
    async def test_scan_dispatches_to_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tdir = Path(tmpdir)
            wf_path = tdir / "wf.yaml"
            yaml.dump(
                {
                    "id": "test-wf",
                    "info": {"name": "T"},
                    "workflows": [{"template": "test/", "matchers": [{"condition": "or"}]}],
                },
                wf_path.open("w"),
            )
            engine = TemplateEngine(templates_dir=tdir)
            with patch.object(engine, "_get_session", new_callable=AsyncMock) as mock_session:
                mock_conn = AsyncMock()
                mock_conn.__aenter__.return_value.status = 404
                mock_conn.__aenter__.return_value.text = AsyncMock(return_value="")
                mock_conn.__aenter__.return_value.headers = {}
                mock_session.return_value.request.return_value = mock_conn
                results = await engine.scan(wf_path, "http://target.com")
                assert isinstance(results, list)
            await engine.close()

    def test_scan_nonexistent_file_raises(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        with pytest.raises(FileNotFoundError):
            asyncio.run(engine.scan(Path("/nonexistent/file.yaml"), "http://target.com"))


class TestTemplateEngineEvents:
    @pytest.mark.asyncio
    async def test_event_bus_emits_template_events(self):
        engine = TemplateEngine(templates_dir=Path("/tmp"))
        events = []
        engine.event_bus.on("template.start", lambda d: events.append(("start", d)))
        engine.event_bus.on("template.complete", lambda d: events.append(("complete", d)))

        template = TemplateDefinition(
            id="event-test",
            info=TemplateInfo(name="Event Test"),
            requests=[TemplateRequest(method="GET", path=["/"])],
        )
        from core.template_engine import TemplateResult

        with patch.object(engine, "_execute_single_request", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = TemplateResult(
                template_id="event-test",
                template_name="Event Test",
                matched=True,
                matched_reason="status 200",
                status_code=200,
                url="http://example.com",
                body="OK",
            )
            await engine.run_template(template, "http://example.com")

        assert any(e[0] == "start" for e in events)
        assert any(e[0] == "complete" for e in events)
        await engine.close()
