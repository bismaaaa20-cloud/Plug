"""Metadata entrypoint for customer-feedback-analysis."""
SKILL_NAME = "customer-feedback-analysis"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
