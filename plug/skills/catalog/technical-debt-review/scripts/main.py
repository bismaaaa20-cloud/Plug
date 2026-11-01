"""Metadata entrypoint for technical-debt-review."""
SKILL_NAME = "technical-debt-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
