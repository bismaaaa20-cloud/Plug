"""Metadata entrypoint for product-copywriting."""
SKILL_NAME = "product-copywriting"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
