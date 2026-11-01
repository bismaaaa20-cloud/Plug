"""Metadata entrypoint for ui-prototyping."""
SKILL_NAME = "ui-prototyping"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
