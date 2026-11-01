"""Metadata entrypoint for customer-success-planning."""
SKILL_NAME = "customer-success-planning"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
