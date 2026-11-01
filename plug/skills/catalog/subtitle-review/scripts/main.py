"""Metadata entrypoint for subtitle-review."""
SKILL_NAME = "subtitle-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
