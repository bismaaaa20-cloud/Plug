"""Metadata entrypoint for web-frontend-accessibility."""
SKILL_NAME = "web-frontend-accessibility"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
