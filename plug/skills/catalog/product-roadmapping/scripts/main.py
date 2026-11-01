"""Metadata entrypoint for product-roadmapping."""
SKILL_NAME = "product-roadmapping"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
