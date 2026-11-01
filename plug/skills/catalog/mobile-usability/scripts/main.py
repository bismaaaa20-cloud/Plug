"""Metadata entrypoint for mobile-usability."""
SKILL_NAME = "mobile-usability"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
