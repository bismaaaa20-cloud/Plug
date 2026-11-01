"""Metadata entrypoint for refactoring."""
SKILL_NAME = "refactoring"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
