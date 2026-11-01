"""Metadata entrypoint for icon-design."""
SKILL_NAME = "icon-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
