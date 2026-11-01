"""Small metadata entrypoint for accessibility-audit skill."""
SKILL_NAME = "accessibility-audit"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
