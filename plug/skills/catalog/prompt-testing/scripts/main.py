"""Metadata entrypoint for prompt-testing."""
SKILL_NAME = "prompt-testing"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
