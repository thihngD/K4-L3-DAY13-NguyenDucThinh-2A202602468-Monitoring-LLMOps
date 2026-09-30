"""Cost optimization before/after on the same workload (bonus, docs/RUBRIC.md H).

Compares the current local prompt template (DEFAULT_PROMPT_TEMPLATE) against
a shorter proposed template on the exact same 10 queries in
data/sample_queries.jsonl, using the same cost formula the app already uses
(LabAgent._estimate_cost).

Honest limitation: FakeLLM.generate() picks output_tokens randomly (80-180)
independent of the prompt, and output tokens dominate cost ($15/1M vs
$3/1M for input) in this mock. So a shorter prompt cannot meaningfully cut
total request cost here - it only reduces the input-token share. This
script isolates that input-side effect by holding output_tokens fixed at
the midpoint of FakeLLM's range for both variants, so the comparison is
attributable purely to prompt length rather than to LLM output randomness.

This is a proposal/analysis only - it does NOT change
app/prompt_management.py's DEFAULT_PROMPT_TEMPLATE, which is a graded
contract (docs/PROMPT_VERSIONING.md) and must not be altered casually.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent import LabAgent
from app.mock_rag import retrieve
from app.prompt_management import DEFAULT_PROMPT_TEMPLATE

OPTIMIZED_TEMPLATE = "F={{feature}}|D={{docs}}|Q={{message}}"
QUERIES_PATH = REPO_ROOT / "data" / "sample_queries.jsonl"

# Midpoint of FakeLLM's random output_tokens range (80-180); held constant
# across both variants so the comparison isolates the input-token effect.
FIXED_OUTPUT_TOKENS = 130


def compile_prompt(template: str, feature: str, docs: list[str], message: str) -> str:
    return (
        template.replace("{{feature}}", feature)
        .replace("{{docs}}", "\n".join(docs))
        .replace("{{message}}", message)
    )


def main() -> None:
    agent = LabAgent()
    queries = [
        json.loads(line)
        for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    print(f"{'query':42} {'in_before':>10} {'in_after':>9} {'cost_before':>12} {'cost_after':>11}")
    total_before = 0.0
    total_after = 0.0
    for q in queries:
        docs = retrieve(q["message"])
        before_prompt = compile_prompt(DEFAULT_PROMPT_TEMPLATE, q["feature"], docs, q["message"])
        after_prompt = compile_prompt(OPTIMIZED_TEMPLATE, q["feature"], docs, q["message"])
        before_tokens_in = max(20, len(before_prompt) // 4)
        after_tokens_in = max(20, len(after_prompt) // 4)
        before_cost = agent._estimate_cost(before_tokens_in, FIXED_OUTPUT_TOKENS)
        after_cost = agent._estimate_cost(after_tokens_in, FIXED_OUTPUT_TOKENS)
        total_before += before_cost
        total_after += after_cost
        print(
            f"{q['message'][:42]:42} {before_tokens_in:>10} {after_tokens_in:>9} "
            f"{before_cost:>12.6f} {after_cost:>11.6f}"
        )

    saved_pct = (1 - total_after / total_before) * 100 if total_before else 0.0
    print()
    print(f"Total cost before : ${total_before:.6f}")
    print(f"Total cost after  : ${total_after:.6f}")
    print(f"Saved             : {saved_pct:.1f}% (input-token share only; output_tokens fixed at "
          f"{FIXED_OUTPUT_TOKENS} for both, since FakeLLM output length is independent of the prompt)")


if __name__ == "__main__":
    main()
