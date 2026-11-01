"""Metadata entrypoint for product-design."""
SKILL_NAME = "product-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
