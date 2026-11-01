"""Metadata entrypoint for requirements-analysis."""
SKILL_NAME = "requirements-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
