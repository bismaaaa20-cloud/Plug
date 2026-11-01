"""Metadata entrypoint for visual-content-strategy."""
SKILL_NAME = "visual-content-strategy"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
