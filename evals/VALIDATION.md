# Validation record — 2026-09-21

## Local executable checks

Environment: Windows, bundled CPython 3.12, python-docx 1.2.0, PyYAML 6.0.3.
PyYAML was installed in a task-local dependency directory; no global package or skill installation was changed.

Commands (Python executable abbreviated as `python`, with task-local PYTHONPATH for PyYAML):

```text
python -X utf8 C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/coherent-academic-writing
  Skill is valid! (exit 0)
python -X utf8 -m unittest discover -s tests -v
  Ran 17 tests — OK (exit 0)
python -m compileall -q skills tests
  exit 0
git diff --check
  exit 0
```

The bundled validator does not support the optional top-level `compatibility` key. Compatibility requirements
are intentionally stored as a string in `metadata.compatibility`, accepted by both this validator and the
Agent Skills metadata contract. The validator was not modified or bypassed. Package tests additionally check
folder/name agreement, self-contained references/license, metadata types and default UI discovery.

Extraction tests use generated synthetic fixtures: full Unicode text beyond the old 200-character preview,
paragraph/table order, source bytes/hash unchanged, nested/merged tables, hyperlink text, nonstandard and
inherited headings, no-heading fallback, incomplete-object warnings, empty/bad DOCX, OLE signature,
resource limits, actual dependency-free subprocess, unique outputs, write-failure cleanup and I/O errors.
The OLE test validates diagnosis wording; it is not a test of decryption or a real encrypted Office document.

## Behavioral forward pass

One independent evaluator agent (inherited model, GPT-6 Astra; no override) received only SKILL.md, routed
references and requests.md. The evaluator did not receive the scoring rubric, implementation discussion or
intended answers. It handled E01–E10 separately within one agent context; these were **not** ten fresh process
or model sessions. Parent review then applied the semantic rubric in README.md to its actual responses.
This is a qualitative forward pass, not a statistical reliability estimate or an automated LLM CI run.

Full responses: [forward-responses.md](results/forward-responses.md). The response preamble describes each
case as independent; the actual isolation level is the single-context, case-by-case procedure just described.

| Case | Result | Observed evidence in the response |
| --- | --- | --- |
| E01 | PASS | C001/C002 retain single-center, age range and noncausal qualification. |
| E02 | PASS | C001 narrows the universal claim; C002 deletes only apology; both datasets and all four numbers remain. |
| E03 | PASS | C002–C004 escalate; no p value, reference or mechanism invented. |
| E04 | PASS | Author-confirmed nonstandard structure accepted; contrary accounts and tentative explanation retained. |
| E05 | PASS | Both proof motivation and convexity condition retained without forced sentence openings. |
| E06 | PASS | Partial coverage reported; image-dependent edits paused; negative evidence retained and universal claim questioned. |
| E07 | PASS | Text-copy P0 exactly equals original minus the approved prefix; P1 is unchanged; evidence-integrity audit supplied. |
| E08 | PASS | Only an unapplied proposal; no claimed file modification or implicit approval of an unseen plan. |
| E09 | PASS | Low-data “only” retained; nonsignificance not converted into equivalence. |
| E10 | PASS | Both negative outcomes remain visible; unsupported conclusion flagged; functional discussion repetition accepted. |

Critical evidence failures: 0 in these cases. No behavior-driven instruction change was needed after this pass.
No DOCX editing, formatting preservation, numerical replication, real journal compliance or reference truth
was tested by the text cases. Those limitations are also explicit in the skill.

## CI

quality.yml defines Windows/Linux × Python 3.10/3.12 unit/package checks, compile checks and committed-diff
whitespace checks. Remote execution status belongs to the PR checks; local success alone is not claimed as
remote CI success. The CI does not require a proprietary local quick_validate path or a model API key.
