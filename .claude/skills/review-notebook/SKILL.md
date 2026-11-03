---
name: review-notebook
description: Review or improve a chapter notebook in this repo (notebooks/NN_*.ipynb) for learners - chapter placement, one experiment per cell with goal and expected outcome, visible prompts and readable model output, clear names, helpers out of cells. Use when the user asks to review, refactor, clean up or improve a notebook, or to apply the chapter 15 improvements to another chapter.
---

# Review a notebook

The rules live in "Notebook quality (the learner's view)" in [AGENTS.md](../../../AGENTS.md), next to the chapter template. That section is the single source of truth, so read it first and follow it. Don't restate or change the rules here.

## Steps

1. Read "Code and notebooks" and "Notebook quality" in `AGENTS.md`, then the reference example: sections 4 and 5 of `notebooks/15_copilot_harness.ipynb` and its helpers in `notebooks/stark_harness.py`.
2. Map the notebook before you change it. Print every cell with its index and type, and list:
   - what it builds on (imports, files, agents, data from other chapters) and which chapters refer to it;
   - every name used in more than one cell (parse the code cells with `ast`);
   - every function defined in a cell;
   - every experiment, and whether it has a goal, inputs and an expected outcome.
3. Report findings to the user first, ordered: story and placement, experiments, visible prompts and output, checks on model output, names, helpers. Propose; don't rewrite the whole notebook in one go.
4. Change one concern per step, in that order, and let the user run the notebook between steps. A live run is the only proof that **Expected:** is true.
5. Edit the `.ipynb` as JSON with a small script: find cells by a unique text marker, assert each replacement matches exactly once, keep cell ids, write LF and `indent=1`. Never rewrite cells you did not mean to touch; the user may have edited them.
6. Check after every step: every code cell parses (`ast.parse`), no name is used before the cell that defines it, the notebook loads as JSON, and the helpers run against a stub client (a `SimpleNamespace` with `output` items) without Azure. Then re-read every markdown cell that describes what you changed (sample prompts, output tables, helper names, **Expected:**) and fix what went stale.
7. When the user pastes output, compare it with **Expected:** and find the cause before changing anything: the code, a rule (skill, script, threshold) or the expectation. Say which, with the evidence.
8. Update `CHANGELOG.md` (edit the chapter's existing `[Unreleased]` line when there is one), the chapter's doc and `story.md` if what the reader sees changed.
9. Before a commit, strip outputs and local kernel metadata, and remove files your test runs created.

## Worked example: chapter 15

What changed from the first version, and which rule it illustrates:

| Before | After | Rule |
|---|---|---|
| chapter 17, after workflows and A2A, though it needs only 13 and 14 | chapter 15, right after Ultron | Place and story |
| considered `14.5` to avoid renumbering | 15 → 16, 16 → 17; README, story acts, docs order, all mentions and the PR text updated | Place and story |
| story and notebook said chapter 07 shows a prompt agent ignoring a skill, after that section was removed | sentence rewritten to what 07 still says | Place and story |
| four cases in one loop over a `CASES` tuple, explained in a table before and a list after | one markdown cell (Goal, inputs, Expected) and one code cell per case | One experiment per cell |
| section 5: ledger question and replay of case A in one cell | three steps: the ledger question in the old conversation, the same question in a new one, then case A in the new one | One experiment per cell |
| case A reused the section 3 conversation, so a re-run found its own invoice as a duplicate | case A opens `invoice_conversation` | One experiment per cell |
| prompt cut at 120 characters, answer at 400 | prompt built in the case cell, shown in full, JSON folded; whole answer as Markdown | Show what the model gets and says |
| long plain-text output, cut by VS Code, answer hidden in the middle | `display(Markdown(...))` with prompt, answer and check table | Show what the model gets and says |
| no idea of the prompt without running the cell | a sample prompt for case A in the markdown | Show what the model gets and says |
| `output_text` glued a preamble and a csv fence into one broken line | `answer_text()` joins messages with blank lines | Show what the model gets and says |
| last expression returned a `Response`, Jupyter printed the repr | display helpers return nothing | Show what the model gets and says |
| `Severity:` checked at the start of all text, broken by a preamble | `follows_escalation()` checks the final message | Checks on model output |
| case A expected `APPROVE` but the skill sent a total with confidence 0.44 to a human | `check_invoice.py` treats amounts the arithmetic confirms as checked (`confirmed_by_arithmetic`) | Checks on model output |
| `pp`, `conv17`, `oai17`, `ALL`, `review`, `jarvis-nb17` | `preview_project`, `sdk_conversation`, `sdk_client`, `ALL_SCRIPTS`, `review_invoice`, `jarvis-nb15` | Names and code |
| eleven functions defined across five cells | `notebooks/stark_harness.py`; the taught calls stay as markdown snippets | Names and code |
| ❓ "the output item type of a shell call was not checked" | `shell_call`, `function_call` (`view`), `/home/session/workspace` from a live run | Facts, not guesses |
| sample prompt without the `confidence` block, "Answer" described as one reply, after the output changed | sample and table updated to what the helpers now show | Facts, not guesses |
