# Framework specification

The four files in this directory are the canonical RUIN framework specification.
They define the analysis protocol, the flag catalogue, the scoring model, and
the output format that any RUIN run must produce.

| File | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | The nine-step analysis protocol — main entry point |
| [flags.md](flags.md) | Flag catalogue: conditions, severities, examples |
| [scoring.md](scoring.md) | Component scores, composite formula, classification bands |
| [output-format.md](output-format.md) | JSON schema for batch output files |

## Runtime independence

The specification is runtime-agnostic. Any LLM agent that can read a paper's
text, follow the protocol, and emit JSON matching the schema can execute RUIN.
The published runs gave every agent text extracted once from each PDF with
`pdftotext -layout`, so that all runs read identical input (see
`reliability/DEVIATIONS.md`).

### Running under Claude Code (skill mode)

A mirror of this directory lives at `.claude/skills/ruin-analysis/` so the
repository works as a Claude Code skill out of the box. After cloning, simply
ask Claude Code:

> Run the ruin-analysis skill on `path/to/batch_folder`.

When editing the specification, update both locations (`framework/` and
`.claude/skills/ruin-analysis/`) to keep them in sync. `framework/` is
canonical; `.claude/skills/ruin-analysis/` is the Claude-Code-specific
install path.

### Running under another LLM runtime

Pass the four documents as system context and the target PDF as the user
message. A minimal harness:

1. Concatenate `SKILL.md` + `flags.md` + `scoring.md` + `output-format.md`
   as the system prompt.
2. Inline the extracted text of the paper to analyse.
3. Instruct the model to emit one JSON object matching the schema in
   `output-format.md`.
4. Persist the JSON as `{output_dir}/{journal_acronym}/{batch_id}.json`.

The published ROMJIST results were produced under Claude Code with Claude Opus
5.5 (`claude-opus-5-5`), one agent per issue, under specification 1.2.0 (tag
`spec-1.2.0`); see the root README and `reliability/`. Record the model
identifier in the batch file's `models` field for any new run. The test-retest
study measured a mean absolute difference of 2.6 points on the 100-point final
score (ICC 0.92), and a second retest of every capped paper reproduced 140 of
the 148 caps.

## Versioning

The specification is versioned independently of the corpus analyses that use
it. Each batch JSON records the `analysis_version` field, so reruns under
later specification revisions can be distinguished from the original baseline.
The current version, 1.2.1, is recorded in [../CHANGELOG.md](../CHANGELOG.md).
Version 1.2.1 states the Necessity Test's combination rule and asks for an
answer to each question; repeating the published runs exactly requires the
1.2.0 files, at tag `spec-1.2.0`.

RUIN is an experimental screen. Its validity against expert judgment has not
been established, and the labels it produces (flags, bands, and the term
"disqualified") mark passages for a reader to examine; they are not findings
about the conduct of any author.
