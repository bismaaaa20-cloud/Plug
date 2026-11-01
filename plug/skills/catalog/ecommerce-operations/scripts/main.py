"""Metadata entrypoint for ecommerce-operations."""
SKILL_NAME = "ecommerce-operations"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
