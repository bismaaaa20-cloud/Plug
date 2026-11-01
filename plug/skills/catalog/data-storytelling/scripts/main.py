"""Metadata entrypoint for data-storytelling."""
SKILL_NAME = "data-storytelling"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
