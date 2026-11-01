"""Metadata entrypoint for customer-journey-mapping."""
SKILL_NAME = "customer-journey-mapping"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
