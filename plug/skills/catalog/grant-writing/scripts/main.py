"""Metadata entrypoint for grant-writing."""
SKILL_NAME = "grant-writing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
