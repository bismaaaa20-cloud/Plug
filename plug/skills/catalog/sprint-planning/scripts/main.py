"""Metadata entrypoint for sprint-planning."""
SKILL_NAME = "sprint-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
