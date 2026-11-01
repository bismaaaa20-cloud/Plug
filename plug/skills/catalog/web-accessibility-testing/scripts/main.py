"""Metadata entrypoint for web-accessibility-testing."""
SKILL_NAME = "web-accessibility-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
