"""Metadata entrypoint for reliability-engineering."""
SKILL_NAME = "reliability-engineering"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
