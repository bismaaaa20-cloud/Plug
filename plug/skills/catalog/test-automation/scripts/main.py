"""Metadata entrypoint for test-automation."""
SKILL_NAME = "test-automation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
