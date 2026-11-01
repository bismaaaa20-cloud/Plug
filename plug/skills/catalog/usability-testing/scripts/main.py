"""Metadata entrypoint for usability-testing."""
SKILL_NAME = "usability-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
