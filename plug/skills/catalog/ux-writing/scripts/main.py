"""Metadata entrypoint for ux-writing."""
SKILL_NAME = "ux-writing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
