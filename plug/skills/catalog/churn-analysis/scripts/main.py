"""Metadata entrypoint for churn-analysis."""
SKILL_NAME = "churn-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
