"""Metadata entrypoint for longform-writing."""
SKILL_NAME = "longform-writing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
