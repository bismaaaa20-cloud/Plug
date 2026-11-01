"""Metadata entrypoint for data-quality-audit."""
SKILL_NAME = "data-quality-audit"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
