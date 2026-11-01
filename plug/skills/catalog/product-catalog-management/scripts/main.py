"""Metadata entrypoint for product-catalog-management."""
SKILL_NAME = "product-catalog-management"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
