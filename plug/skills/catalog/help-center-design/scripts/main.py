"""Metadata entrypoint for help-center-design."""
SKILL_NAME = "help-center-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
