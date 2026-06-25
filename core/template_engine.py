"""
Zen AI Pentest - YAML Template Engine

A Nuclei-inspired engine: loads YAML templates, executes HTTP requests,
evaluates matchers (status/word/regex), extracts values, and resolves
workflow template references via aiohttp.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import yaml

try:
    from core.plugin_manager import EventBus
except ImportError:
    from core.workflow_engine import EventBus

logger = logging.getLogger("ZenAI.TemplateEngine")

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)
MAX_REDIRECTS = 5
_TEMPLATE_BASE = Path(__file__).resolve().parent.parent / "templates"
_DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) ZenAI-TemplateEngine/1.0"


class MatcherType(Enum):
    STATUS = "status"
    WORD = "word"
    REGEX = "regex"


class ExtractorType(Enum):
    REGEX = "regex"
    JSON = "json"


class Severity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Matcher:
    type: MatcherType = MatcherType.WORD
    condition: str = "or"
    status: List[int] = field(default_factory=list)
    words: List[str] = field(default_factory=list)
    regex: List[str] = field(default_factory=list)
    part: str = "body"


@dataclass
class Extractor:
    type: ExtractorType = ExtractorType.REGEX
    name: str = ""
    regex: List[str] = field(default_factory=list)
    json: List[str] = field(default_factory=list)
    part: str = "body"


@dataclass
class TemplateRequest:
    method: str = "GET"
    path: List[str] = field(default_factory=lambda: ["/"])
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    matchers: List[Matcher] = field(default_factory=list)
    extractors: List[Extractor] = field(default_factory=list)


@dataclass
class TemplateInfo:
    name: str = ""
    author: str = ""
    description: str = ""
    severity: Severity = Severity.INFO
    tags: List[str] = field(default_factory=list)


@dataclass
class TemplateDefinition:
    id: str = ""
    info: TemplateInfo = field(default_factory=TemplateInfo)
    requests: List[TemplateRequest] = field(default_factory=list)
    file_path: Optional[Path] = None


@dataclass
class TemplateResult:
    template_id: str = ""
    template_name: str = ""
    matched: bool = False
    matched_reason: str = ""
    extracted: Dict[str, Any] = field(default_factory=dict)
    status_code: int = 0
    url: str = ""
    body: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "matched": self.matched,
            "matched_reason": self.matched_reason,
            "extracted": self.extracted,
            "status_code": self.status_code,
            "url": self.url,
            "error": self.error,
            "execution_time": self.execution_time,
        }


@dataclass
class WorkflowStep:
    template_ref: str = ""
    condition: str = "or"


@dataclass
class WorkflowDefinition:
    id: str = ""
    info: TemplateInfo = field(default_factory=TemplateInfo)
    steps: List[WorkflowStep] = field(default_factory=list)
    file_path: Optional[Path] = None


def _ensure_list(val: Any) -> List:
    if isinstance(val, list):
        return val
    return [val] if val is not None else []


def _parse_matcher(data: Dict[str, Any]) -> Matcher:
    return Matcher(
        type=MatcherType(data.get("type", "word")),
        condition=data.get("condition", "or"),
        status=data.get("status", []),
        words=data.get("words", []),
        regex=data.get("regex", []),
        part=data.get("part", "body"),
    )


def _parse_extractor(data: Dict[str, Any]) -> Extractor:
    return Extractor(
        type=ExtractorType(data.get("type", "regex")),
        name=data.get("name", ""),
        regex=data.get("regex", []),
        json=data.get("json", []),
        part=data.get("part", "body"),
    )


def _parse_request(data: Dict[str, Any]) -> TemplateRequest:
    paths = data.get("path", ["/"])
    if isinstance(paths, str):
        paths = [paths]
    raw_headers = data.get("headers") or {}
    return TemplateRequest(
        method=data.get("method", "GET").upper(),
        path=paths,
        headers=raw_headers,
        body=data.get("body"),
        matchers=[_parse_matcher(m) for m in _ensure_list(data.get("matchers", []))],
        extractors=[_parse_extractor(e) for e in _ensure_list(data.get("extractors", []))],
    )


def _parse_info(data: Dict[str, Any]) -> TemplateInfo:
    sev_str = data.get("severity", "info")
    try:
        severity = Severity(sev_str.lower())
    except ValueError:
        severity = Severity.INFO
    return TemplateInfo(
        name=data.get("name", ""),
        author=data.get("author", ""),
        description=data.get("description", ""),
        severity=severity,
        tags=data.get("tags", []),
    )


def _parse_template(data: Dict[str, Any], file_path: Optional[Path] = None) -> TemplateDefinition:
    return TemplateDefinition(
        id=data.get("id", file_path.stem if file_path else ""),
        info=_parse_info(data.get("info", {})),
        requests=[_parse_request(r) for r in _ensure_list(data.get("requests", []))],
        file_path=file_path,
    )


def _parse_workflow(data: Dict[str, Any], file_path: Optional[Path] = None) -> WorkflowDefinition:
    raw_steps = data.get("workflows", [])
    steps = []
    for s in _ensure_list(raw_steps):
        matchers = _ensure_list(s.get("matchers", []))
        step_condition = matchers[0].get("condition", "or") if matchers else "or"
        steps.append(WorkflowStep(template_ref=s.get("template", ""), condition=step_condition))
    return WorkflowDefinition(
        id=data.get("id", file_path.stem if file_path else ""),
        info=_parse_info(data.get("info", {})),
        steps=steps,
        file_path=file_path,
    )


def _resolve_json_path(data: Any, path: str) -> Any:
    if not path:
        return None
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx] if 0 <= idx < len(current) else None
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current


class TemplateEngine:
    """Nuclei-inspired template engine with workflow support."""

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        event_bus: Optional[EventBus] = None,
        concurrency: int = 10,
        timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
        user_agent: str = _DEFAULT_UA,
    ):
        self.templates_dir = templates_dir or _TEMPLATE_BASE
        self.event_bus = event_bus or EventBus()
        self.concurrency = concurrency
        self.timeout = timeout
        self.user_agent = user_agent
        self._semaphore = asyncio.Semaphore(concurrency)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=self.concurrency, force_close=True)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "TemplateEngine":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
        except (yaml.YAMLError, OSError) as e:
            logger.error("YAML error %s: %s", path, e)
            return None

    def load_template(self, path: Path) -> Optional[TemplateDefinition]:
        data = self._load_yaml(path)
        if data is None:
            return None
        try:
            return _parse_template(data, file_path=path)
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Invalid template %s: %s", path, e)
            return None

    def load_workflow(self, path: Path) -> Optional[WorkflowDefinition]:
        data = self._load_yaml(path)
        if data is None:
            return None
        try:
            return _parse_workflow(data, file_path=path)
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Invalid workflow %s: %s", path, e)
            return None

    def _discover_template_files(self, ref: str) -> List[Path]:
        search_dir = self.templates_dir / ref.strip("/")
        if ref.endswith("/") or search_dir.is_dir():
            if search_dir.is_dir():
                return sorted(search_dir.rglob("*.yaml"))
            return []
        with_suffix = search_dir.with_suffix(".yaml")
        if with_suffix.exists():
            return [with_suffix]
        alt = search_dir.parent / f"{search_dir.name}.yaml"
        if alt.exists():
            return [alt]
        return []

    def resolve_template_ref(self, ref: str) -> List[TemplateDefinition]:
        files = self._discover_template_files(ref)
        templates = []
        for f in files:
            t = self.load_template(f)
            if t is not None:
                templates.append(t)
        return templates

    def _match_status(self, m: Matcher, code: int) -> bool:
        return code in m.status if m.status else False

    def _match_words(self, m: Matcher, body: str) -> bool:
        if not m.words:
            return False
        results = [w in body for w in m.words]
        return all(results) if m.condition == "and" else any(results)

    def _match_regex(self, m: Matcher, body: str) -> bool:
        if not m.regex:
            return False
        results = [bool(re.search(p, body)) for p in m.regex]
        return all(results) if m.condition == "and" else any(results)

    def _evaluate_matchers(self, matchers: List[Matcher], status_code: int, body: str) -> Tuple[bool, str]:
        if not matchers:
            return False, ""
        for m in matchers:
            target = body
            if m.type == MatcherType.STATUS:
                ok = self._match_status(m, status_code)
                reason = f"status {status_code}" if ok else ""
            elif m.type == MatcherType.WORD:
                ok = self._match_words(m, target)
                reason = f"matched words: {[w for w in m.words if w in target]}" if ok else ""
            elif m.type == MatcherType.REGEX:
                ok = self._match_regex(m, target)
                reason = "regex matched" if ok else ""
            else:
                continue
            if ok:
                return True, reason
        return False, ""

    def _execute_extractors(self, extractors: List[Extractor], body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        extracted: Dict[str, Any] = {}
        for ext in extractors:
            source = body
            values: List[str] = []
            if ext.type == ExtractorType.REGEX and ext.regex:
                for pattern in ext.regex:
                    try:
                        values.extend(re.findall(pattern, source))
                    except re.error:
                        pass
            elif ext.type == ExtractorType.JSON and ext.json:
                try:
                    parsed = json.loads(source)
                except (json.JSONDecodeError, TypeError):
                    parsed = {}
                for jp in ext.json:
                    val = _resolve_json_path(parsed, jp)
                    if val is not None:
                        values.extend([str(v) for v in val] if isinstance(val, list) else [str(val)])
            if ext.name:
                extracted[ext.name] = values[0] if len(values) == 1 else values
            else:
                for i, v in enumerate(values):
                    extracted[f"value_{i}"] = v
        return extracted

    def _build_url(self, base: str, path: str) -> str:
        base = base.rstrip("/")
        return f"{base}{path}" if path.startswith("/") else f"{base}/{path}"

    async def _execute_single_request(
        self,
        session: aiohttp.ClientSession,
        req: TemplateRequest,
        target_url: str,
    ) -> TemplateResult:
        result = TemplateResult()
        for path_variant in req.path:
            url = self._build_url(target_url, path_variant)
            result.url = url
            start = time.monotonic()
            try:
                async with self._semaphore:
                    async with session.request(
                        method=req.method,
                        url=url,
                        headers=req.headers or None,
                        data=req.body,
                        allow_redirects=True,
                        max_redirects=MAX_REDIRECTS,
                        ssl=False,
                    ) as resp:
                        status_code = resp.status
                        body = await resp.text(encoding="utf-8", errors="replace")
                        response_headers = dict(resp.headers)
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                result.error = str(e)[:100] if isinstance(e, aiohttp.ClientError) else "Timeout"
                continue
            result.execution_time = time.monotonic() - start
            result.status_code = status_code
            result.body = body
            result.headers = response_headers

            matched, reason = self._evaluate_matchers(req.matchers, status_code, body)
            if matched:
                result.matched = True
                result.matched_reason = f"{result.matched_reason}; {reason}" if result.matched_reason else reason
            result.extracted.update(self._execute_extractors(req.extractors, body, response_headers))
        return result

    async def run_template(self, template: TemplateDefinition, target_url: str) -> TemplateResult:
        session = await self._get_session()
        result = TemplateResult(
            template_id=template.id,
            template_name=template.info.name or template.id,
        )
        await self.event_bus.emit("template.start", {"id": template.id, "target": target_url})
        for req in template.requests:
            r = await self._execute_single_request(session, req, target_url)
            if r.matched:
                result.matched = True
                result.matched_reason = f"{result.matched_reason}; {r.matched_reason}".strip("; ")
            result.extracted.update(r.extracted)
            if not result.body:
                result.body = r.body
                result.status_code = r.status_code or result.status_code
            result.error = result.error or r.error
            result.execution_time += r.execution_time
        await self.event_bus.emit(
            "template.complete",
            {"id": template.id, "target": target_url, "matched": result.matched},
        )
        return result

    async def run_workflow(self, workflow: WorkflowDefinition, target_url: str) -> List[TemplateResult]:
        results: List[TemplateResult] = []
        await self.event_bus.emit("workflow.start", {"id": workflow.id, "target": target_url})
        for step_idx, step in enumerate(workflow.steps):
            logger.info("[%s] Step %d: resolving '%s'", workflow.id, step_idx + 1, step.template_ref)
            templates = self.resolve_template_ref(step.template_ref)
            if not templates:
                logger.warning("No templates for '%s'", step.template_ref)
                continue
            for template in templates:
                try:
                    results.append(await self.run_template(template, target_url))
                except Exception as e:
                    logger.error("Error executing template '%s': %s", template.id, e)
                    results.append(
                        TemplateResult(
                            template_id=template.id,
                            template_name=template.info.name or template.id,
                            error=str(e),
                        )
                    )
        await self.event_bus.emit(
            "workflow.complete",
            {"id": workflow.id, "target": target_url, "total": len(results), "matched": sum(1 for r in results if r.matched)},
        )
        return results

    async def scan(self, path: Union[str, Path], target_url: str) -> List[TemplateResult]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        data = self._load_yaml(path)
        if data is None:
            raise ValueError(f"Failed to parse: {path}")
        if "workflows" in data:
            return await self.run_workflow(_parse_workflow(data, file_path=path), target_url)
        result = await self.run_template(_parse_template(data, file_path=path), target_url)
        return [result]

    def list_templates(self, pattern: Optional[str] = None) -> List[Path]:
        search = self.templates_dir
        return sorted(search.rglob(pattern or "*.yaml"))

    def list_workflows(self) -> List[Path]:
        wf_dir = self.templates_dir / "workflows"
        return sorted(wf_dir.rglob("*.yaml")) if wf_dir.is_dir() else []


async def _demo() -> None:
    """Demonstrate template engine with existing workflow files."""
    logger.info("=" * 56)
    logger.info("  Zen AI Pentest - Template Engine Demo")
    logger.info("=" * 56)
    engine = TemplateEngine()
    workflows = engine.list_workflows()
    logger.info("[+] Found %d workflow(s)", len(workflows))
    for wf in workflows:
        logger.info("    %s", wf.relative_to(engine.templates_dir))

    if not workflows:
        return

    for wf_path in workflows:
        logger.info("\n%s", "─" * 56)
        wf = engine.load_workflow(wf_path)
        if not wf:
            continue
        logger.info("  ID: %s  |  Steps: %d", wf.id, len(wf.steps))
        logger.info("  Name: %s", wf.info.name)
        logger.info("  Description: %s", wf.info.description.strip()[:80])
        for step in wf.steps:
            files = engine._discover_template_files(step.template_ref)
            status = f"{len(files)} template(s)" if files else "(no templates yet)"
            logger.info("    %s %s -> %s", "✓" if files else "·", step.template_ref, status)

    logger.info("\n%s", "─" * 56)
    logger.info("  Engine ready: %s", engine.templates_dir)
    logger.info("  Workflows: %d  |  Concurrency: %d", len(workflows), engine.concurrency)
    logger.info("  Logger: %s  |  EventBus: initialized", logger.name)
    logger.info("=" * 56)


def main() -> None:
    start = time.time()
    try:
        asyncio.run(_demo())
    except KeyboardInterrupt:
        logger.warning("[!] Interrupted")
    logger.info("Done in %.2fs", time.time() - start)


if __name__ == "__main__":
    main()
