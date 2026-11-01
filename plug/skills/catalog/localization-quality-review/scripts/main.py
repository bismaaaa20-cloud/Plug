"""Metadata entrypoint for localization-quality-review."""
SKILL_NAME = "localization-quality-review"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
