"""Metadata entrypoint for competitive-analysis."""
SKILL_NAME = "competitive-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
