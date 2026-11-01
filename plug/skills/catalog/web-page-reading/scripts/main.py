"""Metadata entrypoint for web-page-reading."""
SKILL_NAME = "web-page-reading"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
