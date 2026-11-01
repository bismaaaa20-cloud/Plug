"""Small metadata entrypoint for ui-builder skill."""
SKILL_NAME = "ui-builder"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
