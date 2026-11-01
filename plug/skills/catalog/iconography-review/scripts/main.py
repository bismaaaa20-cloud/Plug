"""Metadata entrypoint for iconography-review."""
SKILL_NAME = "iconography-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
