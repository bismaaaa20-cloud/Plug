"""Metadata entrypoint for experimentation."""
SKILL_NAME = "experimentation"
def run(arguments=None):
    return {"skill": SKILL_NAME, "arguments": dict(arguments or {}), "instructions_file": "SKILL.md"}
