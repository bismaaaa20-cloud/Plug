"""Metadata entrypoint for technical-translation."""
SKILL_NAME = "technical-translation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
