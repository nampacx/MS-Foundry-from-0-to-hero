---
name: write-docs
description: Create or edit documentation in this repo (any .md file such as docs/*.md, README.md, story.md). Use whenever the user asks to document, explain in a doc, write a guide, or update an existing document, so it follows the repo's documentation style and information flow.
---

# Write documentation

The rules live in the "Writing documentation" section of [AGENTS.md](../../../AGENTS.md). That section is the single source of truth, so read it first and follow it. Don't restate or change the rules here.

## Steps

1. Read "Writing documentation" in `AGENTS.md` and the reference example `docs/conversations.md`.
2. Read the code, policies and config the document is about. Take names, values and behaviour from there, not from memory.
3. Outline first: TL;DR, big-picture diagram, numbered sections in the order things happen, optional topics last.
4. Write the document in `docs/` (or edit the existing file). Link to the code instead of copying it.
   Keep emojis sparse: follow the emoji rules in `AGENTS.md` (titles, `##` headings, callouts and status markers only).
5. Mark anything that is demo-grade, not deployed or not planned.
6. Re-read top to bottom for information flow. Check that every link and file name exists.
7. Add the new document to the docs line in `README.md`.
8. Tell the user what you wrote, and what you could not verify.
