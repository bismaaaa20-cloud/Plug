"""Metadata entrypoint for security-testing."""
SKILL_NAME = "security-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
