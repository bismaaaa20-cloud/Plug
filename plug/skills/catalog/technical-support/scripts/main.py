"""Metadata entrypoint for technical-support."""
SKILL_NAME = "technical-support"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
