"""Metadata entrypoint for business-analysis."""
SKILL_NAME = "business-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
