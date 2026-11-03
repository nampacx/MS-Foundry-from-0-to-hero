"""Helpers for chapters 10 and 11: show evaluation results as Markdown.

The notebooks keep the evaluation calls (`evals.create`, `evals.runs.create`); these helpers only read
finished runs and render them: one row per dataset item, one column per evaluator, then the judge's reasons.
"""
from __future__ import annotations

import json

from IPython.display import Markdown, display

from stark_helpers import _d, openai_client, pass_rates


# ---------------------------------------------------------------- reading output items
def _cell(text) -> str:
    """Text that is safe inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def _content(message: dict) -> str:
    """The text of one chat message, whether `content` is a string or a list of parts."""
    content = message.get("content", "")
    if isinstance(content, list):
        return " ".join(str(_d(part).get("text", "")) for part in content)
    return str(content)


def _input_label(source: dict) -> str:
    """What one dataset item asked: the query, the first user message of a conversation, or its id."""
    if source.get("query"):
        return str(source["query"])
    messages = source.get("messages")
    if isinstance(messages, list) and messages:
        first = next((_content(_d(m)) for m in messages if _d(m).get("role") == "user"), _content(_d(messages[0])))
        return f"{first} ({len(messages)} messages)"
    for key in ("conversation_id", "response_id", "id"):
        if source.get(key):
            return f"{key}: {source[key]}"
    return json.dumps(source, default=str)[:200] if source else "(no input)"


def _answer(sample: dict) -> str:
    """The target's answer from an output item's `sample` (empty for runs over saved data)."""
    if sample.get("output_text"):
        return str(sample["output_text"])
    return "\n\n".join(_content(_d(m)) for m in sample.get("output") or [] if _content(_d(m)).strip())


def _mark(result: dict) -> str:
    """✅ / ❌ and the score of one evaluator result."""
    score = result.get("score")
    score = "" if score is None else f" {score:g}" if isinstance(score, (int, float)) else f" {score}"
    passed = result.get("passed")
    return ("✅" if passed else "❌" if passed is False else "–") + score


# ---------------------------------------------------------------- results of one run
def show_scores(eval_id: str, run_id: str, oai=None, reasons: str = "failed") -> None:
    """Show a run as a table (item x evaluator: ✅/❌ and score), then the judge's reasons in full.

    `reasons="failed"` lists the reasons of failed results only, `"all"` lists every reason.
    Conversations and the target's answers are folded under each item, so nothing is cut.
    """
    oai = oai or openai_client()
    items = [_d(i) for i in oai.evals.runs.output_items.list(run_id=run_id, eval_id=eval_id)]
    if not items:
        display(Markdown("_No output items in this run._"))
        return
    criteria = list(dict.fromkeys(_d(r).get("name") for i in items for r in i.get("results") or []))
    md = ["| # | input | " + " | ".join(criteria) + " |", "|---|---|" + "---|" * len(criteria)]
    details = []
    for n, item in enumerate(items, 1):
        source = _d(item.get("datasource_item"))
        results = {_d(r).get("name"): _d(r) for r in item.get("results") or []}
        md.append(f"| {n} | {_cell(_input_label(source))} | "
                  + " | ".join(_mark(results[c]) if c in results else "" for c in criteria) + " |")
        block = []
        if isinstance(source.get("messages"), list):
            turns = "\n\n".join(f"**{_d(m).get('role', '?')}:** {_content(_d(m))}" for m in source["messages"])
            block.append(f"<details><summary>The conversation</summary>\n\n{turns}\n\n</details>")
        answer = _answer(_d(item.get("sample")))
        if answer:
            block.append(f"<details><summary>The agent's answer</summary>\n\n{answer}\n\n</details>")
        block += [f"- **{name}** {_mark(res)}: {res.get('reason') or '(no reason given)'}"
                  for name, res in results.items() if reasons == "all" or res.get("passed") is False]
        if block:
            details += [f"**Item {n}**", ""] + [b + "\n" for b in block]
    note = "reasons of failed results only" if reasons == "failed" else "all reasons"
    md += ["", f"**Per item** ({note})", ""] + (details or ["_nothing failed_"])
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- comparing runs
def show_pass_rates(runs: dict) -> None:
    """Pass rate per evaluator, one column per run: `show_pass_rates({"vague": vague_run, "strict": strict_run})`."""
    rates = {label: pass_rates(run) for label, run in runs.items()}
    criteria = list(dict.fromkeys(c for r in rates.values() for c in r))
    md = ["| evaluator | " + " | ".join(rates) + " |", "|---|" + "---|" * len(rates)]
    for c in criteria:
        cells = [f"{r[c]:.0%}" if c in r and r[c] == r[c] else "–" for r in rates.values()]
        md.append(f"| {c} | " + " | ".join(cells) + " |")
    display(Markdown("\n".join(md)))
