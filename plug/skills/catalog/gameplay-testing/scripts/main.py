"""Metadata entrypoint for gameplay-testing."""
SKILL_NAME = "gameplay-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
