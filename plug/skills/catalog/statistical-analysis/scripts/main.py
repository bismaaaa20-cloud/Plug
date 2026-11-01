"""Metadata entrypoint for statistical-analysis."""
SKILL_NAME = "statistical-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
