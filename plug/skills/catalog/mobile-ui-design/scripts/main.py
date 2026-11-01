"""Metadata entrypoint for mobile-ui-design."""
SKILL_NAME = "mobile-ui-design"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
