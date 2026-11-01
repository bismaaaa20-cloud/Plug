"""Metadata entrypoint for budgeting-analysis."""
SKILL_NAME = "budgeting-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
