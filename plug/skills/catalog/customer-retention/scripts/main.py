"""Metadata entrypoint for customer-retention."""
SKILL_NAME = "customer-retention"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
