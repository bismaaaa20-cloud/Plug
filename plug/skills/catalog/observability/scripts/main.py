"""Metadata entrypoint for observability."""
SKILL_NAME = "observability"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
