"""Metadata entrypoint for governance-review."""
SKILL_NAME = "governance-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
