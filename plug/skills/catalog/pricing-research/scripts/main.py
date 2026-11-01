"""Metadata entrypoint for pricing-research."""
SKILL_NAME = "pricing-research"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
