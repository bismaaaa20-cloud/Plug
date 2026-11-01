"""Metadata entrypoint for financial-model-review."""
SKILL_NAME = "financial-model-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
