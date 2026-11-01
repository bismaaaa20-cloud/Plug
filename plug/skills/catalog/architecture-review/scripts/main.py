"""Metadata entrypoint for architecture-review."""
SKILL_NAME = "architecture-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
