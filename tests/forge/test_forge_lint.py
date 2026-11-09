"""Isolated Git fixtures exercise positive and negative governance gates."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from scripts import forge_lint

TODAY = dt.date(2026, 11, 9)


class ForgeLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "test")
        self.git("config", "user.email", "test@example.invalid")
        self.write(".forge/config.json", '{"schema_version": 1, "markdown_exemptions": {}}')
        self.document("README.md", "DOC-README")
        self.document(".forge/TRACE.md", "DOC-TRACE", body="| Spec | Files |\n| --- | --- |\n")
        self.document(".forge/LEDGER.md", "DOC-LEDGER", body="# Ledger\n")

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args]).decode().strip()

    def write(self, path: str, content: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def document(
        self,
        path: str,
        identifier: str,
        kind: Any = "knowledge",
        status: Any = "ACTIVE",
        body: str = "# Document\n",
        **extra: Any,
    ) -> None:
        meta = {
            "id": identifier,
            "title": "Fixture",
            "type": kind,
            "status": status,
            "version": "1.0.0",
            "owner": "agent",
            "created": "2026-11-01",
            "updated": "2026-11-09",
            "supersedes": [],
            "depends_on": [],
            "implements": [],
            "traces_to": [],
            "tags": [],
            "confidence": "high",
            **extra,
        }
        self.write(path, "---\n" + yaml.safe_dump(meta) + "---\n" + body)

    def problems(self, base: str | None = None) -> list[str]:
        return forge_lint.lint(self.root, base, today=TODAY)

    def assert_problem(self, fragment: str, base: str | None = None) -> None:
        self.assertIn(fragment, "\n".join(self.problems(base)))

    def spec(self, number: int = 1, status: str = "APPROVED", body: str = "# Spec\n") -> None:
        self.document(f"specs/SPEC-{number:03}.md", f"SPEC-{number:03}", "spec", status, body)

    def trace(self, body: str) -> None:
        self.document(".forge/TRACE.md", "DOC-TRACE", body=body)

    def commit(self) -> str:
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def test_clean_repository(self) -> None:
        self.assertEqual([], self.problems())

    def test_missing_frontmatter_in_new_markdown(self) -> None:
        self.write("notes.md", "# No metadata")
        self.assert_problem("missing YAML frontmatter")

    def test_uppercase_extension_is_checked(self) -> None:
        self.write("docs/NEW.MD", "# No metadata")
        self.assert_problem("docs/NEW.MD: missing YAML")

    def test_ignored_markdown_is_not_checked(self) -> None:
        self.write(".gitignore", "cache/\n")
        self.write("cache/vendor.md", "external content")
        self.assertEqual([], self.problems())

    def test_tracked_ignored_markdown_is_still_checked(self) -> None:
        self.write("old.md", "no frontmatter")
        self.git("add", "old.md")
        self.write(".gitignore", "old.md\n")
        self.assert_problem("old.md: missing YAML")

    def test_duplicate_id(self) -> None:
        self.document("other.md", "DOC-README")
        self.assert_problem("duplicate ID")

    def test_duplicate_yaml_field(self) -> None:
        path = self.root / "README.md"
        path.write_text(path.read_text().replace("title: Fixture", "title: One\ntitle: Two"))
        self.assert_problem("duplicate YAML field")

    def test_invalid_status_and_metadata(self) -> None:
        self.document("bad.md", "BAD", "spec", "DONE", owner="robot", version="1")
        for fragment in ("invalid spec lifecycle", "invalid owner", "semver", "spec ID"):
            self.assert_problem(fragment)

    def test_malformed_metadata_does_not_crash(self) -> None:
        self.document("bad.md", "BAD", kind=["spec"], status=["DRAFT"], depends_on="SPEC-001")
        self.assert_problem("unknown document type")
        self.assert_problem("depends_on must be a list")

    def test_non_mapping_yaml(self) -> None:
        self.write("bad.md", "---\n- not a mapping\n---\n")
        self.assert_problem("must be a string-keyed mapping")

    def test_date_validation(self) -> None:
        self.document("bad.md", "BAD", created="2026-11-10", updated="2026-11-08")
        self.assert_problem("created is in the future")
        self.assert_problem("updated precedes created")

    def test_invalid_date(self) -> None:
        self.document("bad.md", "BAD", updated="yesterday")
        self.assert_problem("must be an ISO date")

    def test_unknown_reference(self) -> None:
        self.document("bad.md", "BAD", depends_on=["SPEC-999"])
        self.assert_problem("references unknown ID")

    def test_implements_must_be_spec(self) -> None:
        self.document("bad.md", "BAD", implements=["DOC-README"])
        self.assert_problem("implements must reference a spec")

    def test_dependency_cycle(self) -> None:
        self.document("a.md", "DOC-A", depends_on=["DOC-B"])
        self.document("b.md", "DOC-B", depends_on=["DOC-A"])
        self.assert_problem("dependency cycle")

    def test_legacy_exemption_is_hash_pinned_and_exact(self) -> None:
        text = "Existing legacy reference\n"
        self.write("docs/legacy.MD", text)
        self.write(
            ".forge/config.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "markdown_exemptions": {
                        "docs/legacy.MD": {
                            "reason": "Existing",
                            "sha256": hashlib.sha256(text.encode()).hexdigest(),
                        },
                    },
                }
            ),
        )
        self.assertEqual([], self.problems())
        self.write("docs/another.MD", "Not exempt")
        self.assert_problem("docs/another.MD: missing YAML")
        self.write("docs/legacy.MD", "changed")
        self.assert_problem("legacy exemption hash changed")

    def test_bad_configuration_fails_closed(self) -> None:
        self.write(".forge/config.json", "not json")
        self.assert_problem("invalid configuration")

    def test_source_without_trace(self) -> None:
        self.write("src/example.py", "pass\n")
        self.assert_problem("no spec header or exact TRACE mapping")

    def test_header_can_trace_to_approved_spec(self) -> None:
        self.spec()
        self.write("src/example.py", "# SPEC-001\npass\n")
        self.assertEqual([], self.problems())

    def test_plain_string_is_not_a_header(self) -> None:
        self.spec()
        self.write("src/example.py", 'SPEC = "SPEC-001"\n')
        self.assert_problem("no spec header")

    def test_unknown_or_unapproved_source_spec(self) -> None:
        self.spec(status="DRAFT")
        self.write("src/example.py", "# SPEC-001 SPEC-999\n")
        self.assert_problem("not approved for implementation")
        self.assert_problem("references unknown spec SPEC-999")

    def test_exact_trace_can_cover_binary_source(self) -> None:
        self.spec()
        self.write("src/icon.bin", "binary")
        self.trace("| SPEC-001 | `src/icon.bin` |\n")
        self.assertEqual([], self.problems())
        self.write("src/another.bin", "unmapped")
        self.assert_problem("src/another.bin: no spec header")

    def test_trace_typo_is_rejected(self) -> None:
        self.spec()
        self.trace("| SPEC-001 | `src/missing.py` |\n")
        self.assert_problem("references missing file")

    def test_implemented_spec_needs_acceptance_criteria(self) -> None:
        self.spec(status="IMPLEMENTED")
        self.assert_problem("implemented spec needs numbered ACs")

    def test_each_acceptance_criterion_needs_its_own_test(self) -> None:
        self.spec(status="IMPLEMENTED", body="- AC-1: Example\n- AC-2: Other\n")
        self.write("tests/test_example.py", "def test_ac_1_example():\n    pass\n")
        self.trace("| SPEC-001 | `tests/test_example.py` |\n")
        self.assert_problem("AC-2 missing named test")
        self.write("tests/test_example.py", "def test_ac_1_a(): pass\ndef test_ac_2_b(): pass\n")
        self.assertEqual([], self.problems())

    def test_different_specs_cannot_borrow_same_numbered_test(self) -> None:
        self.spec(status="IMPLEMENTED", body="- AC-1: First\n")
        self.spec(2, status="VERIFIED", body="- AC-1: Second\n")
        self.write("tests/test_first.py", "def test_ac_1_first(): pass\n")
        self.trace("| SPEC-001 | `tests/test_first.py` |\n")
        self.assert_problem("specs/SPEC-002.md: AC-1 missing named test")

    def test_reference_to_spec_in_other_column_does_not_assign_test(self) -> None:
        self.spec(1, status="IMPLEMENTED", body="- AC-1: First\n")
        self.spec(2, status="IMPLEMENTED", body="- AC-1: Second\n")
        self.write("tests/test_first.py", "def test_ac_1_first(): pass\n")
        self.trace("| SPEC-001 | `tests/test_first.py` | relates to SPEC-002 |\n")
        self.assert_problem("specs/SPEC-002.md: AC-1 missing named test")

    def test_stale_doing_task(self) -> None:
        self.document(
            "tasks/DOING/T-001.md",
            "T-001",
            "task",
            "DOING",
            "## Verification\n`true`\n",
            updated="2026-11-06",
        )
        self.assert_problem("DOING task is stale")

    def test_task_within_48h(self) -> None:
        self.document(
            "tasks/DOING/T-001.md",
            "T-001",
            "task",
            "DOING",
            "## Verification\n`true`\n",
            updated="2026-11-07",
        )
        self.assertEqual([], self.problems())

    def test_task_directory_and_blocker(self) -> None:
        self.document("tasks/OPEN/T-001.md", "T-001", "task", "BLOCKED")
        self.assert_problem("task directory must match status")
        self.assert_problem("BLOCKED task needs a written question")
        self.assert_problem("task needs a Verification section")

    def test_product_task_needs_real_plan(self) -> None:
        self.spec()
        self.document(
            "tasks/OPEN/T-001.md",
            "T-001",
            "task",
            "OPEN",
            "## Verification\n`true`\n",
            implements=["SPEC-001"],
            plan="PLAN-999",
        )
        self.assert_problem("product task needs a real plan ID")

    def test_list_configuration_fails_closed(self) -> None:
        self.write(".forge/config.json", "[]")
        self.assert_problem("configuration must be a mapping")

    def test_invalid_spec_status_list_does_not_crash(self) -> None:
        self.document("specs/SPEC-001.md", "SPEC-001", "spec", ["IMPLEMENTED"])
        self.assert_problem("invalid spec lifecycle status")

    def test_valid_blocked_task(self) -> None:
        self.document(
            "tasks/REVIEW/T-001.md",
            "T-001",
            "task",
            "BLOCKED",
            "## Verification\n`true`\n## Notes\nBLOCKED: Need a human decision.\n",
        )
        self.assertEqual([], self.problems())

    def test_source_append_when_ledger_did_not_exist_in_base(self) -> None:
        self.spec()
        ledger = self.root / ".forge/LEDGER.md"
        previous = ledger.read_text()
        ledger.unlink()
        base = self.commit()
        ledger.write_text(previous + "\n## First session\nCreated source.\n")
        self.write("src/example.py", "# SPEC-001\n")
        self.assertEqual([], self.problems(base))

    def test_source_change_requires_ledger_append(self) -> None:
        self.spec()
        base = self.commit()
        self.write("src/example.py", "# SPEC-001\n")
        self.assert_problem("src changes require a nonempty append", base)
        with (self.root / ".forge/LEDGER.md").open("a") as file:
            file.write("\n## New session\nRecorded work.\n")
        self.assertEqual([], self.problems(base))

    def test_ledger_rewrite_cannot_replace_append(self) -> None:
        self.spec()
        base = self.commit()
        self.write("src/example.py", "# SPEC-001\n")
        path = self.root / ".forge/LEDGER.md"
        path.write_text(path.read_text().replace("# Ledger", "# Changed") + "\nNew entry\n")
        self.assert_problem("preserving old bytes", base)

    def test_blank_ledger_append_fails(self) -> None:
        self.spec()
        base = self.commit()
        self.write("src/example.py", "# SPEC-001\n")
        with (self.root / ".forge/LEDGER.md").open("a") as file:
            file.write("\n   \n")
        self.assert_problem("nonempty append", base)

    def test_source_deletion_requires_handoff(self) -> None:
        self.spec()
        self.write("src/example.py", "# SPEC-001\n")
        base = self.commit()
        (self.root / "src/example.py").unlink()
        self.assert_problem("nonempty append", base)

    def test_unchanged_source_does_not_require_append(self) -> None:
        self.spec()
        self.write("src/example.py", "# SPEC-001\n")
        base = self.commit()
        self.document("other.md", "OTHER")
        self.assertEqual([], self.problems(base))

    def test_committed_source_changes_compared_with_pr_base(self) -> None:
        self.spec()
        base = self.commit()
        self.write("src/example.py", "# SPEC-001\n")
        self.commit()
        self.assert_problem("nonempty append", base)

    def test_invalid_base_fails_closed(self) -> None:
        self.assert_problem("ledger base check failed", "not-a-real-revision")


if __name__ == "__main__":
    unittest.main()
