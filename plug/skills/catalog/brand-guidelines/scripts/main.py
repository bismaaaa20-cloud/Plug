"""Metadata entrypoint for brand-guidelines."""
SKILL_NAME = "brand-guidelines"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
