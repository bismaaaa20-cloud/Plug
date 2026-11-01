"""Metadata entrypoint for product-analytics."""
SKILL_NAME = "product-analytics"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
