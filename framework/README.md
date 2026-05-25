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

The specification is runtime-agnostic. Any LLM agent that can ingest a PDF,
follow the protocol, and emit JSON matching the schema can execute RUIN.

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
2. Attach (or inline the text of) the PDF to analyse.
3. Instruct the model to emit one JSON object matching the schema in
   `output-format.md`.
4. Persist the JSON as `{output_dir}/{journal_acronym}/{batch_id}.json`.

The published ROMJIST results were produced under Claude Code. Any equivalent
runtime should reproduce the headline figures to within the test-retest
variance reported in the manuscript (mean absolute deviation 3.2 points on
the 100-point final score).

## Versioning

The specification is versioned independently of the corpus analyses that use
it. Each batch JSON records the `analysis_version` field, so reruns under
later specification revisions can be distinguished from the original baseline.
The current version is recorded in [../CHANGELOG.md](../CHANGELOG.md).
