"""Metadata entrypoint for data-engineering."""
SKILL_NAME = "data-engineering"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
