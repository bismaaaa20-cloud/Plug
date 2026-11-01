"""Metadata entrypoint for documentation-review."""
SKILL_NAME = "documentation-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
