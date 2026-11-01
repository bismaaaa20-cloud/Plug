"""Metadata entrypoint for typography-review."""
SKILL_NAME = "typography-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
