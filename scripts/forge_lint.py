#!/usr/bin/env python3
"""Structural SPEC-FORGE checks. Does not assert semantic or human approval correctness."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

STATES = {
    "brainstorm": {"SEED", "GROWING", "PROMOTED", "ABANDONED"},
    "spec": {
        "DRAFT",
        "REVIEW",
        "APPROVED",
        "IMPLEMENTING",
        "IMPLEMENTED",
        "VERIFIED",
        "DEPRECATED",
    },
    "adr": {"PROPOSED", "ACCEPTED", "SUPERSEDED"},
    "plan": {"DRAFT", "ACTIVE", "COMPLETE", "ARCHIVED"},
    "task": {"OPEN", "DOING", "REVIEW", "DONE", "BLOCKED"},
}
for _kind in (
    "vision",
    "knowledge",
    "ops",
    "quality",
    "governance",
    "ledger",
    "state",
    "glossary",
    "trace",
    "index",
    "template",
):
    STATES[_kind] = {"DRAFT", "ACTIVE", "ARCHIVED"}
REQUIRED = {
    "id",
    "title",
    "type",
    "status",
    "version",
    "owner",
    "created",
    "updated",
    "supersedes",
    "depends_on",
    "implements",
    "traces_to",
    "tags",
    "confidence",
}
SPEC_ID = re.compile(r"\bSPEC-\d+\b")
LIST_FIELDS = {"supersedes", "depends_on", "implements", "traces_to", "tags"}


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate fields instead of silently replacing them."""


def unique_mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)  # type: ignore[no-untyped-call]
        if key in result:
            raise ValueError(f"duplicate YAML field {key!r}")
        result[key] = loader.construct_object(value_node)  # type: ignore[no-untyped-call]
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"git {' '.join(args[:2])} failed: {result.stderr.decode().strip()}")
    return result.stdout


def date_value(value: object) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return dt.date.fromisoformat(value)
    raise ValueError("must be an ISO date (YYYY-MM-DD)")


def parse_doc(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("unterminated YAML frontmatter")
    data = yaml.load("".join(lines[1:end]), Loader=UniqueLoader)
    if not isinstance(data, dict) or any(not isinstance(k, str) for k in data):
        raise ValueError("frontmatter must be a string-keyed mapping")
    return data, "".join(lines[end + 1 :])


def trace_rows(text: str) -> dict[str, set[str]]:
    """Spec and paths must be in the same Markdown table row (no global test reuse)."""
    rows: dict[str, set[str]] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = line.split("|")
        # Only the Spec column establishes ownership, not mentions elsewhere in a row.
        for spec in SPEC_ID.findall(cells[1] if len(cells) > 1 else ""):
            rows.setdefault(spec, set()).update(re.findall(r"`([^`]+)`", line))
    return rows


def header_specs(path: Path) -> set[str]:
    lines = path.read_bytes().decode("utf-8", errors="replace").splitlines()[:20]
    return {
        spec
        for line in lines
        if re.match(r"\s*(?:#|//|/\*|\*|<!--)", line)
        for spec in SPEC_ID.findall(line)
    }


def lint(root: Path, base: str | None = None, today: dt.date | None = None) -> list[str]:
    now = dt.datetime.combine(today, dt.time.min, dt.UTC) if today else dt.datetime.now(dt.UTC)
    today = now.date()
    errors: list[str] = []
    try:
        paths = {
            name.decode("utf-8")
            for name in git(
                root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"
            ).split(b"\0")
            if name
        }
    except ValueError as exc:
        return [str(exc)]
    try:
        config = json.loads((root / ".forge/config.json").read_text())
        if not isinstance(config, dict):
            raise ValueError("configuration must be a mapping")
        if config.get("schema_version") != 1:
            raise ValueError("unsupported schema_version")
        exemptions = config["markdown_exemptions"]
        if not isinstance(exemptions, dict):
            raise ValueError("markdown_exemptions must be a mapping")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f".forge/config.json: invalid configuration: {exc}"]

    for path, record in exemptions.items():
        if (
            not isinstance(record, dict)
            or not record.get("reason")
            or not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", "")))
        ):
            errors.append(f"{path}: exemption needs a reason and SHA-256")
        elif path not in paths or not (root / path).is_file():
            errors.append(f"{path}: exempt legacy file is missing")
        elif hashlib.sha256((root / path).read_bytes()).hexdigest() != record["sha256"]:
            errors.append(f"{path}: legacy exemption hash changed; migration needs human review")

    docs: dict[str, tuple[str, dict[str, Any], str]] = {}
    for path in sorted(paths):
        file = root / path
        if not path.lower().endswith(".md") or path.startswith("src/") or path in exemptions:
            continue
        if not file.is_file():
            continue  # A local deletion is handled by Git/PR review, not a read crash.
        try:
            meta, body = parse_doc(file.read_text())
        except (OSError, UnicodeError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        validation_start = len(errors)
        missing = REQUIRED - meta.keys()
        if missing:
            errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
        for key in REQUIRED - LIST_FIELDS:
            if key in {"created", "updated"}:
                continue
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                errors.append(f"{path}: {key} must be a nonempty string")
        kind, status = meta.get("type"), meta.get("status")
        if not isinstance(kind, str) or kind not in STATES:
            errors.append(f"{path}: unknown document type {kind!r}")
        elif not isinstance(status, str) or status not in STATES[kind]:
            errors.append(f"{path}: invalid {kind} lifecycle status {status!r}")
        if meta.get("owner") not in ("human", "agent", "pair"):
            errors.append(f"{path}: invalid owner")
        if meta.get("confidence") not in ("low", "medium", "high"):
            errors.append(f"{path}: invalid confidence")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(meta.get("version", ""))):
            errors.append(f"{path}: version must be semver X.Y.Z")
        for key in LIST_FIELDS:
            value = meta.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                errors.append(f"{path}: {key} must be a list of strings")
        dates: dict[str, dt.date] = {}
        for key in ("created", "updated"):
            try:
                dates[key] = date_value(meta.get(key))
                if dates[key] > today:
                    errors.append(f"{path}: {key} is in the future")
            except ValueError as exc:
                errors.append(f"{path}: {key} {exc}")
        if len(dates) == 2 and dates["updated"] < dates["created"]:
            errors.append(f"{path}: updated precedes created")
        identifier = meta.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Z][A-Z0-9-]*", identifier):
            errors.append(f"{path}: invalid ID")
        elif identifier in docs:
            errors.append(f"{path}: duplicate ID {identifier} (also {docs[identifier][0]})")
        if kind == "spec" and not SPEC_ID.fullmatch(str(identifier)):
            errors.append(f"{path}: spec ID must be SPEC-<number>")
        if kind == "task":
            if not re.search(r"^## Verification\s*$", body, re.MULTILINE):
                errors.append(f"{path}: task needs a Verification section")
            parts = Path(path).parts
            folder = "REVIEW" if status == "BLOCKED" else status
            if len(parts) != 3 or parts[0] != "tasks" or parts[1] != folder:
                errors.append(f"{path}: task directory must match status ({folder})")
            if status == "BLOCKED" and not re.search(r"BLOCKED:\s*\S", body):
                errors.append(f"{path}: BLOCKED task needs a written question")
            if status == "DOING" and "updated" in dates:
                # Date-only values represent UTC midnight; exactly 48h is still allowed.
                updated_at = dt.datetime.combine(dates["updated"], dt.time.min, dt.UTC)
                if now - updated_at > dt.timedelta(hours=48):
                    errors.append(f"{path}: DOING task is stale (>48h)")
        if len(errors) == validation_start and isinstance(identifier, str):
            docs[identifier] = (path, meta, body)

    for identifier, (path, meta, _body) in docs.items():
        for field in ("depends_on", "supersedes", "implements"):
            refs = meta.get(field, [])
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if not isinstance(ref, str) or ref not in docs:
                    errors.append(f"{path}: {field} references unknown ID {ref!r}")
                elif ref == identifier:
                    errors.append(f"{path}: {field} cannot reference itself")
                elif field == "implements" and docs[ref][1].get("type") != "spec":
                    errors.append(f"{path}: implements must reference a spec: {ref}")
        if meta.get("type") == "task":
            if meta.get("implements"):
                plan = meta.get("plan")
                if not isinstance(plan, str) or plan not in docs or docs[plan][1]["type"] != "plan":
                    errors.append(f"{path}: product task needs a real plan ID")

    # Detect dependency cycles without relying on recursive depth.
    dependencies = {
        identifier: {
            ref for ref in meta.get("depends_on", []) if isinstance(ref, str) and ref in docs
        }
        if isinstance(meta.get("depends_on"), list)
        else set()
        for identifier, (_, meta, _) in docs.items()
    }
    while dependencies:
        ready = {key for key, refs in dependencies.items() if not refs}
        if not ready:
            errors.append(f"dependency cycle involving: {', '.join(sorted(dependencies))}")
            break
        dependencies = {key: refs - ready for key, refs in dependencies.items() if key not in ready}

    trace_file = root / ".forge/TRACE.md"
    rows = trace_rows(trace_file.read_text()) if trace_file.is_file() else {}
    for spec, files in rows.items():
        if spec not in docs or docs[spec][1].get("type") != "spec":
            errors.append(f"TRACE: unknown spec {spec}")
        for path in files:
            if path.startswith(("src/", "tests/")) and path not in paths:
                errors.append(f"TRACE: {spec} references missing file {path}")
    allowed = {"APPROVED", "IMPLEMENTING", "IMPLEMENTED", "VERIFIED"}
    for path in sorted(paths):
        if not path.startswith("src/") or not (root / path).is_file():
            continue
        linked = header_specs(root / path) | {spec for spec, files in rows.items() if path in files}
        if not linked:
            errors.append(f"{path}: no spec header or exact TRACE mapping")
        for spec in linked:
            if spec not in docs or docs[spec][1].get("type") != "spec":
                errors.append(f"{path}: references unknown spec {spec}")
            elif docs[spec][1].get("status") not in allowed:
                errors.append(f"{path}: {spec} is not approved for implementation")
    for identifier, (path, meta, body) in docs.items():
        if meta.get("type") != "spec" or meta.get("status") not in {"IMPLEMENTED", "VERIFIED"}:
            continue
        criteria = set(re.findall(r"^\s*(?:[-*]\s+)?(?:\*\*)?AC-(\d+)\b", body, re.MULTILINE))
        if not criteria:
            errors.append(f"{path}: implemented spec needs numbered ACs")
        test_text = "\n".join(
            (root / file).read_text(errors="replace")
            for file in rows.get(identifier, set())
            if file.startswith("tests/") and file in paths and (root / file).is_file()
        )
        for criterion in sorted(criteria):
            if not re.search(rf"\b(?:def|function)\s+test_ac_{criterion}_\w+\s*\(", test_text):
                errors.append(f"{path}: AC-{criterion} missing named test on its TRACE row")

    if base:
        try:
            # Validate as a revision before using it in a diff range or object lookup.
            resolved = (
                git(
                    root,
                    "rev-parse",
                    "--verify",
                    "--end-of-options",
                    f"{base}^{{commit}}",
                )
                .decode()
                .strip()
            )
            source_changes = any(
                p.startswith(b"src/")
                for p in git(
                    root,
                    "diff",
                    "--name-only",
                    "-z",
                    resolved,
                    "--",
                    "src/",
                ).split(b"\0")
            )
            untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", "src/")
            if source_changes or untracked.strip(b"\0"):
                existing = git(root, "ls-tree", "--name-only", resolved, "--", ".forge/LEDGER.md")
                old = git(root, "show", f"{resolved}:.forge/LEDGER.md") if existing else b""
                current = (root / ".forge/LEDGER.md").read_bytes()
                if not current.startswith(old) or not current[len(old) :].strip():
                    errors.append(
                        "LEDGER: src changes require a nonempty append, preserving old bytes"
                    )
        except (ValueError, OSError) as exc:
            errors.append(f"ledger base check failed: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--base", help="Actual PR base commit; enables append-only ledger diff check"
    )
    args = parser.parse_args()
    problems = lint(args.root.resolve(), args.base)
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        print(f"forge-lint: FAIL ({len(problems)} errors)")
        return 1
    mode = "PR ledger diff checked" if args.base else "no PR base supplied; ledger diff not checked"
    print(f"forge-lint: PASS ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
