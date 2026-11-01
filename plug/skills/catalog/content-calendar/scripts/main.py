"""Metadata entrypoint for content-calendar."""
SKILL_NAME = "content-calendar"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
