"""Helper entrypoint for the ui-ux-design skill."""

SKILL_NAME = "ui-ux-design"

def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
