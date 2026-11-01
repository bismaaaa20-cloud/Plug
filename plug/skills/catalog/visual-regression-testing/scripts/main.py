"""Metadata entrypoint for visual-regression-testing."""
SKILL_NAME = "visual-regression-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
